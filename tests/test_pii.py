from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd_and_payment_card() -> None:
    cccd = scrub_text("CCCD: 079123456789")
    card = scrub_text("Card: 4111 1111 1111 1111")

    assert "079123456789" not in cccd
    assert "REDACTED_CCCD" in cccd
    assert "4111 1111 1111 1111" not in card
    assert "REDACTED_CREDIT_CARD" in card


def test_scrub_passport_and_labeled_vietnamese_address() -> None:
    passport = scrub_text("Passport: B12345678")
    address = scrub_text("Địa chỉ: 12 Nguyễn Huệ, Quận 1, TP HCM")

    assert "B12345678" not in passport
    assert "REDACTED_PASSPORT_VN" in passport
    assert "12 Nguyễn Huệ" not in address
    assert "REDACTED_ADDRESS" in address

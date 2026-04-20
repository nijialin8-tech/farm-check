"""Tests for i18n module."""
import i18n


def test_default_language():
    """Test that default language is zh_TW."""
    assert i18n.get_current_language() == 'zh_TW'


def test_set_language_english():
    """Test setting language to English."""
    result = i18n.set_language('en')
    assert result is True
    assert i18n.get_current_language() == 'en'
    # Reset to default
    i18n.set_language('zh_TW')


def test_set_language_chinese():
    """Test setting language to Traditional Chinese."""
    result = i18n.set_language('zh_TW')
    assert result is True
    assert i18n.get_current_language() == 'zh_TW'


def test_set_invalid_language():
    """Test that invalid language code returns False."""
    original_lang = i18n.get_current_language()
    result = i18n.set_language('invalid')
    assert result is False
    assert i18n.get_current_language() == original_lang


def test_translation_without_args():
    """Test basic translation without arguments."""
    i18n.set_language('en')
    assert i18n.t('program_title') == '=== Timer Program ==='

    i18n.set_language('zh_TW')
    assert i18n.t('program_title') == '=== 計時器程式 ==='


def test_translation_with_single_arg():
    """Test translation with single format argument."""
    i18n.set_language('en')
    assert i18n.t('press_to_start', 'F1') == 'Press [F1] to START/RESET'

    i18n.set_language('zh_TW')
    assert i18n.t('press_to_start', 'F1') == '按 [F1] 開始/重置'


def test_translation_with_multiple_args():
    """Test translation with multiple format arguments."""
    i18n.set_language('en')
    result = i18n.t('random_offset_example', 125, 135)
    assert '125' in result and '135' in result

    i18n.set_language('zh_TW')
    result = i18n.t('random_offset_example', 125, 135)
    assert '125' in result and '135' in result


def test_missing_translation_key():
    """Test that missing keys return the key itself."""
    result = i18n.t('nonexistent_key')
    assert result == 'nonexistent_key'


def test_translation_with_invalid_format():
    """Test that invalid format arguments don't crash."""
    # Should handle gracefully if args don't match format string
    result = i18n.t('press_to_start')  # Missing required arg
    # Should return the text even if formatting fails
    assert result is not None


def test_all_languages_have_same_keys():
    """Test that all languages define the same keys."""
    en_keys = set(i18n.LANGUAGES['en'].keys())
    zh_keys = set(i18n.LANGUAGES['zh_TW'].keys())

    # Check for missing keys in either language
    missing_in_zh = en_keys - zh_keys
    missing_in_en = zh_keys - en_keys

    assert len(missing_in_zh) == 0, f"Keys missing in zh_TW: {missing_in_zh}"
    assert len(missing_in_en) == 0, f"Keys missing in en: {missing_in_en}"


def test_language_consistency():
    """Test that switching languages persists correctly."""
    i18n.set_language('en')
    assert i18n.t('program_title') == '=== Timer Program ==='

    i18n.set_language('zh_TW')
    assert i18n.t('program_title') == '=== 計時器程式 ==='

    i18n.set_language('en')
    assert i18n.t('program_title') == '=== Timer Program ==='

#!/usr/bin/env python3
"""Translate this project's Russian ESPHome log messages to English on the fly.

Standalone filter, lives outside esphome/ so it never conflicts with
upstream changes. Pipe device logs through it:

    esphome logs esphome/config.yaml | python3 tools/translate_log.py

Any line that doesn't match a known message (including non-log output,
or a message added upstream after this dictionary was last updated) is
passed through unchanged.
"""
import re
import sys

# Matches a single printf-style specifier, e.g. %d, %.2f, %02X, %s, %%
SPEC_RE = re.compile(r"%(?:\.\d+f|\d*d|\d*u|\d*X|\d*x|s|%)")


def _spec_regex(spec: str) -> str:
    if spec == "%%":
        return re.escape("%")
    if spec.endswith("f"):
        decimals = spec[1:-1]  # e.g. ".1" from "%.1f", "" from "%f"
        if decimals in ("", ".0"):
            return r"-?\d+"
        return r"-?\d+\.\d+"
    if spec.endswith(("d", "u")):
        return r"-?\d+"
    if spec.endswith(("X", "x")):
        return r"[0-9A-Fa-f]+"
    if spec.endswith("s"):
        return r".*"
    return re.escape(spec)


def _compile_pattern(fmt: str) -> re.Pattern:
    parts = []
    pos = 0
    for m in SPEC_RE.finditer(fmt):
        parts.append(re.escape(fmt[pos:m.start()]))
        parts.append("(" + _spec_regex(m.group()) + ")")
        pos = m.end()
    parts.append(re.escape(fmt[pos:]))
    return re.compile("".join(parts))


def _build_replacer(ru_fmt: str, en_fmt: str):
    pattern = _compile_pattern(ru_fmt)
    en_specs = list(SPEC_RE.finditer(en_fmt))

    def replace(match: re.Match) -> str:
        result = []
        pos = 0
        for i, spec_m in enumerate(en_specs):
            result.append(en_fmt[pos:spec_m.start()])
            result.append(match.group(i + 1))
            pos = spec_m.end()
        result.append(en_fmt[pos:])
        return "".join(result)

    return pattern, replace


# Extracted from every Russian ESP_LOG*() call in esphome/. Regenerate by
# grepping for ESP_LOG[EWIDV]("tag", "...") calls containing Cyrillic text.
TRANSLATIONS = [
    ("BLE клиент подключён: Training Status = Idle (0x01)", "BLE client connected: Training Status = Idle (0x01)"),
    ("Control Point ← 0x%02X (%d байт): %s", "Control Point ← 0x%02X (%d bytes): %s"),
    ("Control Point → ответ 0x80 0x%02X 0x%02X", "Control Point → response 0x80 0x%02X 0x%02X"),
    ("Free Run активен, регулировка скорости по пульсу приостановлена", "Free Run active, heart-rate speed control paused"),
    ("Free Run активен, регулировка скорости приостановлена", "Free Run active, speed control paused"),
    ("Free Run активен, управление по пульсу приостановлено", "Free Run active, heart-rate control paused"),
    ("Free Run включён, предыдущий режим: %d", "Free Run enabled, previous mode: %d"),
    ("Free Run выключен, восстановлен режим: %d", "Free Run disabled, restored mode: %d"),
    ("Free Running Mode отключен: switch=%d, active=%d", "Free Running Mode disabled: switch=%d, active=%d"),
    ("HIIT завершён: выполнено %d циклов", "HIIT finished: completed %d cycles"),
    ("HIIT стартовал, цикл счётчик сброшен", "HIIT started, cycle counter reset"),
    ("Pause — выполнен", "Pause — executed"),
    ("Request Control подтверждён", "Request Control confirmed"),
    ("Request Control — успех", "Request Control — success"),
    ("Resume — выполнен", "Resume — executed"),
    ("Set Speed → %.1f км/ч (FTMS Target Speed Changed 0x05)", "Set Speed → %.1f km/h (FTMS Target Speed Changed 0x05)"),
    ("Start отклонён защитой", "Start rejected by safety guard"),
    ("Start — запуск выполнен", "Start — startup executed"),
    ("Start — тренажёр уже работает", "Start — treadmill already running"),
    ("Stop — выполнен", "Stop — executed"),
    ("Target Incline отклонён: %.1f%%", "Target Incline rejected: %.1f%%"),
    ("Target Speed отклонён: %.2f км/ч", "Target Speed rejected: %.2f km/h"),
    ("Target Speed → %.2f км/ч", "Target Speed → %.2f km/h"),
    ("manual_stop сброшен в 0 после 5 секунд", "manual_stop reset to 0 after 5 seconds"),
    ("Бегун в безопасной зоне: %.0f см", "Runner in safe zone: %.0f cm"),
    ("Бегун вне безопасного диапазона (%.0f см), вызываем паузу", "Runner outside safe range (%.0f cm), triggering pause"),
    ("Возвращено ручное управление", "Manual control restored"),
    ("Возвращено управление по пульсу", "Heart-rate control restored"),
    ("Длина дорожки вне диапазона: %d см, установлено 100 см", "Belt length out of range: %d cm, set to 100 cm"),
    ("Задняя зона (первый шаг): -%.1f км/ч, новая цель %.1f", "Rear zone (first step): -%.1f km/h, new target %.1f"),
    ("Задняя зона: -%.1f км/ч, новая цель %.1f", "Rear zone: -%.1f km/h, new target %.1f"),
    ("Запуск калибровки скорости", "Starting speed calibration"),
    ("Запуск программы", "Starting program"),
    ("Запуск ручного режима", "Starting manual mode"),
    ("Зона замедления вне диапазона: %d см, установлено 62 см", "Deceleration zone out of range: %d cm, set to 62 cm"),
    ("Зона ускорения вне диапазона: %d см, установлено 35 см", "Acceleration zone out of range: %d cm, set to 35 cm"),
    ("Игнорируем частую команду наклона", "Ignoring frequent incline command"),
    ("Инициализация при старте: Training Status = Idle (0x01)", "Startup initialization: Training Status = Idle (0x01)"),
    ("Калибровка завершена: min=%d см, max=%d см, длина=%d см, accel=%d см, decel=%d см", "Calibration finished: min=%d cm, max=%d cm, length=%d cm, accel=%d cm, decel=%d cm"),
    ("Калибровка начата, скорость установлена на 4 км/ч", "Calibration started, speed set to 4 km/h"),
    ("Кнопка калибровки нажата", "Calibration button pressed"),
    ("Команда Start проигнорирована: тренажёр остановлен вручную", "Start command ignored: treadmill stopped manually"),
    ("Команда Start проигнорирована: тренажёр уже работает", "Start command ignored: treadmill already running"),
    ("Команда: %s, Значение: %s", "Command: %s, Value: %s"),
    ("Команда: 0x%02X, Данные: %d байт, motor_running=%d, manual_stop=%d", "Command: 0x%02X, Data: %d bytes, motor_running=%d, manual_stop=%d"),
    ("Максимальное расстояние вне диапазона: %d см, установлено 85 см", "Maximum distance out of range: %d cm, set to 85 cm"),
    ("Минимальное расстояние вне диапазона: %d см, установлено 25 см", "Minimum distance out of range: %d cm, set to 25 cm"),
    ("Мотор не активен, безопасная остановка не требуется", "Motor not active, safety stop not required"),
    ("Наклон обновлен: %d", "Incline updated: %d"),
    ("Наклон обратной связи обновлен: %d", "Incline feedback updated: %d"),
    ("Наклон установлен: %.1f%%, уведомление: Target Incline Changed (0x06)", "Incline set: %.1f%%, notification: Target Incline Changed (0x06)"),
    ("Начало High: мгновенная корректировка скорости по пульсу", "Start of High: instant heart-rate speed adjustment"),
    ("Начальная позиция: %.0f см", "Initial position: %.0f cm"),
    ("Начальная скорость: 1.0 км/ч", "Initial speed: 1.0 km/h"),
    ("Не найдено команд в формате [КОМАНДА:ЗНАЧЕНИЕ]: %s", "No commands found in [COMMAND:VALUE] format: %s"),
    ("Недопустимая скорость: %.2f км/ч", "Invalid speed: %.2f km/h"),
    ("Недопустимый наклон: %.1f%%", "Invalid incline: %.1f%%"),
    ("Неизвестная команда Control Point: 0x%02X", "Unknown Control Point command: 0x%02X"),
    ("Неизвестная команда обработана: %s=%s", "Unknown command processed: %s=%s"),
    ("Неизвестная команда: %s=%s", "Unknown command: %s=%s"),
    ("Неизвестная команда: 0x%02X", "Unknown command: 0x%02X"),
    ("Некорректная скорость: %s", "Invalid speed: %s"),
    ("Некорректный наклон: %s", "Invalid incline: %s"),
    ("Новое максимальное расстояние: %.1f см", "New maximum distance: %.1f cm"),
    ("Новое минимальное расстояние: %.1f см", "New minimum distance: %.1f cm"),
    ("Одно из основных значений равно NaN", "One of the core values is NaN"),
    ("Ответ отправлен на Control Point", "Response sent to Control Point"),
    ("Ответ отправлен: 0x%02X", "Response sent: 0x%02X"),
    ("Отправка команды на дисплей - наклон", "Sending command to display - incline"),
    ("Отправка команды на дисплей - скорость", "Sending command to display - speed"),
    ("Отправлено уведомление: %s (0x%02X)", "Notification sent: %s (0x%02X)"),
    ("Отправлено уведомление: Cool Down (0x0B)", "Notification sent: Cool Down (0x0B)"),
    ("Отправлено уведомление: High Intensity Interval (0x04)", "Notification sent: High Intensity Interval (0x04)"),
    ("Отправлено уведомление: Idle (0x01)", "Notification sent: Idle (0x01)"),
    ("Отправлено уведомление: Manual Mode (0x0D)", "Notification sent: Manual Mode (0x0D)"),
    ("Отправлено уведомление: Other (0x00)", "Notification sent: Other (0x00)"),
    ("Отправлено уведомление: Paused (0x02)", "Notification sent: Paused (0x02)"),
    ("Отправлено уведомление: Resumed (0x04)", "Notification sent: Resumed (0x04)"),
    ("Отправлено уведомление: Started or Resumed (0x04)", "Notification sent: Started or Resumed (0x04)"),
    ("Отправлено уведомление: Stopped or Paused (0x02)", "Notification sent: Stopped or Paused (0x02)"),
    ("Отправлено уведомление: Training Status %s (0x%02X), remaining cycles: %d", "Notification sent: Training Status %s (0x%02X), remaining cycles: %d"),
    ("Отправлено уведомление: Warming Up (0x02)", "Notification sent: Warming Up (0x02)"),
    ("Ошибка датчика расстояния, вызываем паузу", "Distance sensor error, triggering pause"),
    ("Ошибка датчика расстояния, запуск невозможен", "Distance sensor error, cannot start"),
    ("Ошибка: недостаточно данных с датчика", "Error: insufficient sensor data"),
    ("Передняя зона: +%.1f км/ч, новая цель %.1f", "Front zone: +%.1f km/h, new target %.1f"),
    ("Переключение на заднюю зону", "Switching to rear zone"),
    ("Переключение на страницу 1", "Switching to page 1"),
    ("Переход на страницу → %d", "Switching to page → %d"),
    ("Получена команда RSC: 0x%02X, Данные: %d байт", "Received RSC command: 0x%02X, Data: %d bytes"),
    ("Получено: %s", "Received: %s"),
    ("Попытка повторного запуска, игнорируется", "Restart attempt ignored"),
    ("Проверка интервала: switch=%d, active=%d, is_active=%d, auto_mode=%d", "Interval check: switch=%d, active=%d, is_active=%d, auto_mode=%d"),
    ("Режим не активен", "Mode not active"),
    ("Режим свободного бега запущен", "Free running mode started"),
    ("Режим свободного бега: запущен (0x04)", "Free running mode: started (0x04)"),
    ("Скорость обновлена: %d", "Speed updated: %d"),
    ("Скорость обратной связи обновлена: %d", "Speed feedback updated: %d"),
    ("Скорость установлена (goal): %.2f км/ч", "Speed set (goal): %.2f km/h"),
    ("Слишком длинная команда или значение: %s", "Command or value too long: %s"),
    ("Стоп выполнен", "Stop executed"),
    ("Текущая скорость для калибровки: %.2f км/ч", "Current speed for calibration: %.2f km/h"),
    ("Установлен HIIT (control_mode = 0), иконка 62", "HIIT set (control_mode = 0), icon 62"),
    ("Установлен режим управления по пульсу (control_mode = 2), иконка 59", "Heart-rate control mode set (control_mode = 2), icon 59"),
    ("Установлен ручной режим (control_mode = 0), иконка 62", "Manual mode set (control_mode = 0), icon 62"),
]

# Longest literal text first, so a specific message (e.g. a fixed "Idle
# (0x01)" notification) wins over a shorter, more generic %s/%02X template
# that would otherwise also match it.
_COMPILED = sorted(
    (_build_replacer(ru, en) for ru, en in TRANSLATIONS),
    key=lambda pair: -len(pair[0].pattern),
)


def translate_line(line: str) -> str:
    for pattern, replace in _COMPILED:
        new_line, n = pattern.subn(replace, line)
        if n:
            return new_line
    return line


def main() -> None:
    for line in sys.stdin:
        sys.stdout.write(translate_line(line))
        sys.stdout.flush()


if __name__ == "__main__":
    main()

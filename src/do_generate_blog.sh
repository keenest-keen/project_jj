#!/usr/bin/env bash
# генератор блога - из json-постов в итоговые html-файлы

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

# ---------- Значения по умолчанию ----------
DEFAULT_INPUT="../posts_json"
DEFAULT_OUTPUT="../blog"
posts_override="../posts_override"

# ---------- Хелперы ----------
ask_yes_no() {
    local prompt="$1" default="$2" answer
    if [ "$default" = "y" ]; then
        read -rp "$prompt [Y/n]: " answer
        answer="${answer:-y}"
    else
        read -rp "$prompt [y/N]: " answer
        answer="${answer:-n}"
    fi
    case "${answer,,}" in
        y|yes|д|да) return 0 ;;
        *)          return 1 ;;
    esac
}

# ---------- Опрос ----------
echo "=== Генератор блога ==="
echo

read -rp "Входная папка  (--json-dir)  [$DEFAULT_INPUT]:  " INPUT_DIR
INPUT_DIR="${INPUT_DIR:-$DEFAULT_INPUT}"

read -rp "Выходная папка (--output-dir) [$DEFAULT_OUTPUT]: " OUTPUT_DIR
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"

CLEAN="n"
if ask_yes_no "Очищать выходную папку перед генерацией?" y; then
    CLEAN="y"
fi

USE_OVERRIDE="n"
if ask_yes_no "Копировать из posts_override? (существующие *.json сохранятся как *.original)" n; then
    USE_OVERRIDE="y"
fi

PRIVATE="n"
if ask_yes_no "Запустить с флагом --private?" n; then
    PRIVATE="y"
fi

# ---------- Абсолютные пути ----------
INPUT_ABS="$(realpath -m -- "$INPUT_DIR")"
OUTPUT_ABS="$(realpath -m -- "$OUTPUT_DIR")"
OVERRIDE_ABS="$(realpath -m -- "$posts_override")"

echo
echo "--- Параметры запуска ---"
printf '  Входная папка:  %s\n' "$INPUT_ABS"
printf '  Выходная папка: %s\n' "$OUTPUT_ABS"
printf '  Очистка выхода: %s\n' "$CLEAN"
printf '  Cache override: %s (%s)\n' "$USE_OVERRIDE" "$OVERRIDE_ABS"
printf '  --private:      %s\n' "$PRIVATE"
echo

read -rp "Продолжить? [Y/n]: " CONFIRM
CONFIRM="${CONFIRM:-y}"
case "${CONFIRM,,}" in
    y|yes|д|да) ;;
    *) echo "Отменено."; exit 0 ;;
esac

# ---------- Очистка выхода ----------
if [ "$CLEAN" = "y" ] && [ -d "$OUTPUT_ABS" ]; then
    echo "Удаляю $OUTPUT_ABS ..."
    rm -rf -- "$OUTPUT_ABS"
fi

# ---------- Копирование из posts_override с бэкапом ----------
if [ "$USE_OVERRIDE" = "y" ]; then
    if [ -d "$OVERRIDE_ABS" ]; then
        echo "Копирую из $OVERRIDE_ABS в $INPUT_ABS ..."
        mkdir -p -- "$INPUT_ABS"
        while IFS= read -r -d '' src; do
            rel="${src#"$OVERRIDE_ABS"/}"
            dst="$INPUT_ABS/$rel"

            # Существующий *.json -> *.original (один раз)
            if [ -e "$dst" ] \
               && [[ "$dst" == *.json ]] \
               && [[ "$dst" != *.original ]]; then
                orig="${dst%.json}.original"
                if [ ! -e "$orig" ]; then
                    mv -- "$dst" "$orig"
                    echo "  backup: $rel -> $(basename -- "$orig")"
                fi
            fi

            mkdir -p -- "$(dirname -- "$dst")"
            cp -f -- "$src" "$dst"
        done < <(find "$OVERRIDE_ABS" -type f -print0)
    else
        echo "ПРЕДУПРЕЖДЕНИЕ: $OVERRIDE_ABS не найдена, пропускаю копирование." >&2
    fi
fi

# ---------- Запуск генератора ----------
echo
echo "Запуск генератора..."
cd "$SCRIPT_DIR/generator"

ARGS=(--json-dir "$INPUT_ABS" --output-dir "$OUTPUT_ABS" -v)
[ "$PRIVATE" = "y" ] && ARGS+=(--private)

python3 main.py "${ARGS[@]}"

echo "Готово."
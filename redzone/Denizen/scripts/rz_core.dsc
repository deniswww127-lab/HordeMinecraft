# ==========================================================================
#  RED ZONE — Ядро модуля выживания
#  Конфигурация, отключение саморегенерации, сброс травм при возрождении.
#  Игра: Minecraft 1.20.4 | Движок: Denizen
# ==========================================================================

# --------------------------------------------------------------------------
#  Настройки модуля. Меняешь значения здесь -> в игре /rz setup (без рестарта).
#  Все настройки хранятся в server-флагах, чтобы их читали остальные скрипты.
# --------------------------------------------------------------------------
rz_setup:
    type: task
    debug: false
    script:
    # --- Пороги веса (кг) ---
    - flag server rz_light_max:25         # выше этого — нельзя бежать (спринт)
    - flag server rz_heavy_max:35         # выше этого — еле идёт
    - flag server rz_default_weight:0.2   # вес предмета, которого нет в таблице
    # --- Медицина ---
    - flag server rz_bleed_chance:40      # шанс открыть кровотечение с попадания, %
    - flag server rz_fracture_min_dmg:4   # минимальный урон падения для перелома, HP
    # --- Таблица весов предметов (кг за 1 шт.) ---
    # Боевой лут будет носить персональный флаг rz_weight (см. item-скрипты),
    # эта таблица — фолбэк для ванильных материалов.
    - flag server rz_weights:!
    - flag server rz_weights:<map[arrow=0.03;iron_ingot=1;gold_ingot=1.2;copper_ingot=0.8;diamond=0.4;emerald=0.05;netherite_ingot=2;iron_block=9;gold_block=10.8;diamond_block=3.6;bread=0.3;cooked_beef=0.4;apple=0.2;golden_apple=0.4;potion=0.5;iron_sword=1.5;iron_pickaxe=1.5;iron_axe=1.6;shield=2.5;bow=0.8;crossbow=1.5;iron_helmet=1.5;iron_chestplate=4;iron_leggings=3;iron_boots=1.2;diamond_helmet=2;diamond_chestplate=5;diamond_leggings=4;diamond_boots=1.5;cobblestone=0.5;stone=0.5;dirt=0.4;oak_log=0.7;paper=0.2;stick=0.4;clay_ball=0.8]>
    - announce to_console "<&a>[RED ZONE] Конфигурация модуля выживания загружена."

# --------------------------------------------------------------------------
#  Глобальные события ядра.
# --------------------------------------------------------------------------
rz_core_world:
    type: world
    debug: false
    events:
        # При старте сервера применяем конфигурацию.
        after server start:
        - run rz_setup

        # ХАРДКОР: тело не лечится само от сытости. Только бинты/аптечки/медблок.
        # (Голодные раны REGEN/SATIATED отменяем, магию/зелья оставляем.)
        on player heals:
        - if <context.reason> == REGEN || <context.reason> == SATIATED:
            - determine cancelled

        # Свежий старт после смерти — снимаем все травмы и сбрасываем штрафы.
        on player respawns:
        - flag <player> rz_bleeding:!
        - flag <player> rz_fracture:!
        - flag <player> rz_using_medical:!
        - adjust <player> food_level:20
        - adjust <player> walk_speed:0.2

# ==========================================================================
#  RED ZONE — Отладочная команда /rz (требует право rz.admin или OP)
#  Для тестирования модуля выживания на dev-сервере.
# ==========================================================================

rz_admin_command:
    type: command
    debug: false
    name: rz
    description: RED ZONE — отладка модуля выживания.
    usage: /rz <give|bleed|fracture|heal|weight|setup>
    permission: rz.admin
    script:
    - if !<player.is_online>:
        - narrate "Эта команда предназначена для игрока в игре."
        - stop
    - define sub <context.args.get[1]||help>
    - choose <[sub]>:
        - case give:
            - define what <context.args.get[2]||all>
            - define amt <context.args.get[3]||1>
            - choose <[what]>:
                - case bandage:
                    - give rz_bandage quantity:<[amt]>
                - case splint:
                    - give rz_splint quantity:<[amt]>
                - case medkit:
                    - give rz_medkit quantity:<[amt]>
                - case all:
                    - give rz_bandage quantity:3
                    - give rz_splint quantity:2
                    - give rz_medkit quantity:1
                - default:
                    - narrate "<&c>Неизвестный предмет: <[what]>"
                    - stop
            - narrate "<&a>Выдано."
        - case bleed:
            - flag <player> rz_bleeding
            - narrate "<&c>Кровотечение запущено."
        - case fracture:
            - flag <player> rz_fracture
            - narrate "<&c>Перелом ноги установлен."
        - case heal:
            - flag <player> rz_bleeding:!
            - flag <player> rz_fracture:!
            - heal <player>
            - narrate "<&a>Полностью вылечены, травмы сняты."
        - case weight:
            - narrate "<&e>Текущий груз: <player.flag[rz_weight_current]||0> кг"
            - narrate "<&7>Порог бега: <server.flag[rz_light_max]||25> кг | Перегруз: <server.flag[rz_heavy_max]||35> кг"
        - case setup:
            - run rz_setup
            - narrate "<&a>Конфигурация перезагружена."
        - default:
            - narrate "<&6>=== RED ZONE — отладка ==="
            - narrate "<&7>/rz give <bandage|splint|medkit|all> [кол-во]"
            - narrate "<&7>/rz bleed <&8>— запустить кровотечение"
            - narrate "<&7>/rz fracture <&8>— сломать ногу"
            - narrate "<&7>/rz heal <&8>— вылечить всё"
            - narrate "<&7>/rz weight <&8>— показать груз"
            - narrate "<&7>/rz setup <&8>— перезагрузить конфиг"

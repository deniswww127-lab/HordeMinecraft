# ==========================================================================
#  RED ZONE — Применение медикаментов (Tension Medicine)
#  ПКМ запускает «каст» с анимацией ожидания. Полученный урон прерывает каст,
#  предмет не расходуется. Игрок во время каста почти обездвижен (см. rz_weight).
# ==========================================================================

rz_use_world:
    type: world
    debug: false
    events:
        on player right clicks:
        # Определяем тип медикамента: сначала по флагу предмета,
        # затем — фолбэк по имени item-скрипта (на случай, если флаги не легли).
        - define med <context.item.flag[rz_medical]||none>
        - if <[med]> == none:
            - define sn <context.item.script.name||none>
            - if <[sn]> == rz_bandage:
                - define med bandage
            - else if <[sn]> == rz_splint:
                - define med splint
            - else if <[sn]> == rz_medkit:
                - define med medkit
        - if <[med]> == none:
            - stop
        # Нельзя применять два медикамента одновременно (защита от двойного клика).
        - if <player.has_flag[rz_using_medical]>:
            - stop
        - run rz_use_medical def:<[med]>

# --------------------------------------------------------------------------
#  Каст применения медикамента.
# --------------------------------------------------------------------------
rz_use_medical:
    type: task
    debug: false
    definitions: med
    script:
    # Параметры по типу медикамента.
    - choose <[med]>:
        - case bandage:
            - define secs 3
            - define verb "Перевязываю рану"
        - case splint:
            - define secs 4
            - define verb "Накладываю шину"
        - case medkit:
            - define secs 5
            - define verb "Использую аптечку"
        - default:
            - stop
    # Проверки целесообразности (не тратим медикамент впустую).
    - if <[med]> == bandage && !<player.has_flag[rz_bleeding]>:
        - actionbar "<&7>Кровотечения нет." targets:<player>
        - stop
    - if <[med]> == splint && !<player.has_flag[rz_fracture]>:
        - actionbar "<&7>Перелома нет." targets:<player>
        - stop
    - if <[med]> == medkit && <player.health> >= <player.health_max>:
        - actionbar "<&7>Здоровье уже полное." targets:<player>
        - stop
    # Запускаем каст.
    - flag <player> rz_using_medical expire:<duration[<[secs].add[3]>s]>
    - flag <player> rz_cast_cancelled:false
    - actionbar "<&e><[verb]>..." targets:<player>
    - playsound <player> sound:block_wool_place volume:1 pitch:1
    - wait <duration[<[secs]>s]>
    # Проверки после ожидания.
    - if !<player.is_online>:
        - stop
    - if <player.flag[rz_cast_cancelled]||false>:
        - flag <player> rz_using_medical:!
        - actionbar "<&c>Применение прервано — вы получили урон!" targets:<player>
        - playsound <player> sound:entity_item_break
        - stop
    # Успех: расходуем предмет и применяем эффект.
    - take scriptname:rz_<[med]> quantity:1
    - flag <player> rz_using_medical:!
    - choose <[med]>:
        - case bandage:
            - flag <player> rz_bleeding:!
            - actionbar "<&a>Рана перевязана. Кровотечение остановлено." targets:<player>
        - case splint:
            - flag <player> rz_fracture:!
            - actionbar "<&a>Шина наложена. Нога зафиксирована." targets:<player>
        - case medkit:
            - heal 8 <player>
            - actionbar "<&a>Аптечка использована." targets:<player>
    - playsound <player> sound:entity_player_levelup pitch:1.5

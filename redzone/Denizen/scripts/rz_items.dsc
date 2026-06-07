# ==========================================================================
#  RED ZONE — Медицинские предметы (item-скрипты)
#  Материалы временные: на этапе ресурс-пака заменим на воксельные модели
#  через custom_model_data. Флаг rz_weight задаёт вес для системы груза,
#  флаг rz_medical — тип медикамента для обработчика применения.
# ==========================================================================

rz_bandage:
    type: item
    debug: false
    material: paper
    display name: <&c><&l>Бинт
    lore:
    - <&7>Останавливает кровотечение.
    - <&8>ПКМ — наложить (3 сек)
    - <&8>Вес: 0.2 кг
    flags:
        rz_weight: 0.2
        rz_medical: bandage

rz_splint:
    type: item
    debug: false
    material: stick
    display name: <&f><&l>Шина
    lore:
    - <&7>Фиксирует сломанную ногу.
    - <&8>ПКМ — наложить (4 сек)
    - <&8>Вес: 0.4 кг
    flags:
        rz_weight: 0.4
        rz_medical: splint

rz_medkit:
    type: item
    debug: false
    material: clay_ball
    display name: <&a><&l>Аптечка
    lore:
    - <&7>Восстанавливает 8 HP (4 сердца).
    - <&8>ПКМ — использовать (5 сек)
    - <&8>Вес: 0.8 кг
    flags:
        rz_weight: 0.8
        rz_medical: medkit

# ==========================================================================
#  RED ZONE — Система веса, штрафы передвижения и HUD (босс-бар)
#  «Жадность убивает»: чем больше тащишь, тем медленнее двигаешься.
# ==========================================================================

rz_weight_world:
    type: world
    debug: false
    events:
        # Раз в секунду пересчитываем вес и обновляем HUD у всех онлайн-игроков.
        on delta time secondly:
        - foreach <server.online_players> as:p:
            - run rz_player_tick def:<[p]>

# --------------------------------------------------------------------------
#  Посекундный тик на одного игрока: вес -> штрафы -> HUD.
# --------------------------------------------------------------------------
rz_player_tick:
    type: task
    debug: false
    definitions: p
    script:
    # --- 1. Суммарный вес содержимого инвентаря ---
    - define total 0
    - foreach <[p].inventory.list_contents> as:item:
        - if <[item].material.name> == air:
            - foreach next
        - define unit <[item].flag[rz_weight]||<server.flag[rz_weights].get[<[item].material.name>]||<server.flag[rz_default_weight]||0.2>>>
        - define total <[total].add[<[unit].mul[<[item].quantity>]>]>
    - define total <[total].round_to[2]>
    - flag <[p]> rz_weight_current:<[total]>
    # --- 2. Штрафы передвижения ---
    - define lmax <server.flag[rz_light_max]||25>
    - define hmax <server.flag[rz_heavy_max]||35>
    - if <[p].has_flag[rz_using_medical]>:
        # во время применения медикамента игрок почти обездвижен
        - adjust <[p]> walk_speed:0.05
        - adjust <[p]> food_level:6
    - else if <[total]> >= <[hmax]> || <[p].has_flag[rz_fracture]>:
        # перегруз ИЛИ перелом: еле идёт, без бега
        - adjust <[p]> walk_speed:0.12
        - adjust <[p]> food_level:6
    - else if <[total]> >= <[lmax]>:
        # тяжело: ходит нормально, но бежать не может
        - adjust <[p]> walk_speed:0.2
        - adjust <[p]> food_level:6
    - else:
        # налегке: полная подвижность
        - adjust <[p]> walk_speed:0.2
        - adjust <[p]> food_level:20
    # --- 3. HUD ---
    - run rz_hud_update def:<[p]>

# --------------------------------------------------------------------------
#  Обновление персонального босс-бара: HP + Груз + статусы травм.
#  Босс-бар выбран сознательно — actionbar занят патронами WeaponMechanics.
# --------------------------------------------------------------------------
rz_hud_update:
    type: task
    debug: false
    definitions: p
    script:
    - define hp <[p].health.round>
    - define hpmax <[p].health_max.round>
    - define frac <[p].health.div[<[p].health_max>].min[1]>
    - define weight <[p].flag[rz_weight_current]||0>
    - define lmax <server.flag[rz_light_max]||25>
    - define hmax <server.flag[rz_heavy_max]||35>
    # цвет полосы и HP — по уровню здоровья
    - define color GREEN
    - define hpcolor <&a>
    - if <[frac]> <= 0.25:
        - define color RED
        - define hpcolor <&c>
    - else if <[frac]> <= 0.5:
        - define color YELLOW
        - define hpcolor <&e>
    # цвет груза — по порогам веса
    - define wcolor <&a>
    - if <[weight]> >= <[hmax]>:
        - define wcolor <&4>
    - else if <[weight]> >= <[lmax]>:
        - define wcolor <&6>
    # индикаторы травм
    - define status ""
    - if <[p].has_flag[rz_bleeding]>:
        - define status "<[status]> <&4>[КРОВЬ]"
    - if <[p].has_flag[rz_fracture]>:
        - define status "<[status]> <&c>[НОГА]"
    - define title "<[hpcolor]>HP <[hp]>/<[hpmax]>  <&8>|  <[wcolor]>Груз <[weight]>/<[lmax]>кг<[status]>"
    - bossbar rz_hud_<[p].uuid> "players:<[p]>" "title:<[title]>" progress:<[frac]> color:<[color]> style:SOLID

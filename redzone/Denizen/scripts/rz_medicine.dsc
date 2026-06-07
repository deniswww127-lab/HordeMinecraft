# ==========================================================================
#  RED ZONE — Хардкор-медицина: кровотечение и переломы
#  Здоровье не регенерирует (см. rz_core). Травмы лечатся только медикаментами.
# ==========================================================================

rz_medicine_world:
    type: world
    debug: false
    events:
        # Получение урона -> шанс травмы + прерывание текущей перевязки.
        on player damaged:
        # Любой ощутимый урон прерывает применение медикамента.
        - if <player.has_flag[rz_using_medical]>:
            - flag <player> rz_cast_cancelled:true
        - define cause <context.cause>
        # Пулевые и рукопашные ранения -> шанс кровотечения.
        - if <[cause]> == ENTITY_ATTACK || <[cause]> == ENTITY_SWEEP_ATTACK || <[cause]> == PROJECTILE:
            - if !<player.has_flag[rz_bleeding]> && <util.random.int[1].to[100]> <= <server.flag[rz_bleed_chance]||40>:
                - flag <player> rz_bleeding
                - playsound <player> sound:entity_player_hurt volume:0.7 pitch:0.8
                - actionbar "<&4>Открылось кровотечение! Нужен бинт." targets:<player>
        # Падения -> перелом ноги при достаточном уроне.
        - else if <[cause]> == FALL:
            - if <context.final_damage> >= <server.flag[rz_fracture_min_dmg]||4> && !<player.has_flag[rz_fracture]>:
                - flag <player> rz_fracture
                - playsound <player> sound:entity_player_attack_crit pitch:0.5
                - actionbar "<&c>Перелом ноги! Нужна шина." targets:<player>

        # Тик кровотечения — раз в 4 секунды снимаем по 1 HP (половина сердца).
        on delta time secondly every:4:
        - foreach <server.online_players> as:p:
            - if <[p].has_flag[rz_bleeding]>:
                - hurt 1 <[p]>
                - playsound <[p]> sound:entity_player_hurt volume:0.5 pitch:1.3

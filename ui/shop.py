import pygame
from systems.upgrade_system import UPGRADES

def draw_shop_hint(surface, font, npc_role, upgrade_system, player_gold):
    """
    يرسم واجهة المتجر ديناميكياً بناءً على حالة نظام الترقيات
    ويغير لون السعر بناءً على توفر الذهب لدى اللاعب.
    """
    options = UPGRADES.get(npc_role, [])
    if not options:
        return

    # إعدادات أبعاد اللوحة
    panel_x, panel_y = 45, 348
    panel_w, panel_h = 480, 30 + len(options) * 28 + 14

    # إنشاء خلفية اللوحة
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((8, 10, 20, 210))

    # تحديد لون النمط بناءً على الدور
    role_col = {
        "blacksmith": (220, 160, 30),
        "healer":     (60,  200, 100),
    }.get(npc_role, (100, 180, 220))

    # رسم الحدود
    pygame.draw.rect(panel, (*role_col, 160), (0, 0, panel_w, panel_h), 1, border_radius=8)
    pygame.draw.rect(panel, (*role_col, 80),  (0, 0, panel_w, 4), border_radius=8)
    surface.blit(panel, (panel_x, panel_y))

    # العنوان
    role_lbl = font.render(f"{npc_role.capitalize()} Shop  ·  press key to buy", True, role_col)
    surface.blit(role_lbl, (panel_x + 12, panel_y + 8))

    # حلقة عرض الخيارات
    for i, (name, base_cost, key) in enumerate(options, start=1):
        # استعلام السعر والمستوى من النظام
        cost = upgrade_system.get_cost(key, base_cost)
        row_y = panel_y + 32 + (i - 1) * 28

        # تحديد نص الترقية (اسم + مستوى/أقصى مستوى)
        if key != "heal":
            level = upgrade_system.get_level(key)
            max_level = upgrade_system.get_max_level(key)
            display_name = f"{name} {level}/{max_level}"
            cost_str = "MAX" if level >= max_level else f"◆ {cost}"
        else:
            display_name = name
            cost_str = f"◆ {cost}"

        # تحديد لون السعر: أحمر إذا كان الذهب غير كافٍ، ذهبي إذا كان كافياً
        if cost_str != "MAX" and player_gold < cost:
            cost_color = (230, 60, 60)  # أحمر
        else:
            cost_color = (220, 180, 40) # ذهبي

        # رسم شارة المفتاح (Badge)
        badge = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.rect(badge, (40, 50, 80, 200), (0, 0, 22, 22), border_radius=4)
        pygame.draw.rect(badge, (80, 100, 160, 160), (0, 0, 22, 22), 1, border_radius=4)
        k_surf = font.render(str(i), True, (180, 200, 255))
        badge.blit(k_surf, k_surf.get_rect(center=(11, 11)))
        surface.blit(badge, (panel_x + 10, row_y))

        # رسم اسم الترقية
        n_surf = font.render(display_name, True, (210, 210, 220))
        surface.blit(n_surf, (panel_x + 40, row_y + 2))

        # رسم تكلفة الذهب باللون المحدد
        cost_surf = font.render(cost_str, True, cost_color)
        surface.blit(cost_surf, (panel_x + panel_w - 70, row_y + 2))
# جرد الرسم البرمجي

## ما حُوّل في هذه الدفعة

| العنصر | رابط الأصل | المصدر القابل للتحرير |
|---|---|---|
| شحن الداش | fx_dash_charge | assets/visuals/dash_charge.svg |
| تحديد Airstrike | fx_airstrike_target | assets/visuals/airstrike_target.svg |
| ظهور رمز إيقاف الزمن | fx_time_sigil | assets/visuals/time_sigil.svg |
| هالة Feast / Blood Moon | fx_vampire_aura | إعادة استخدام ring.png بلون مستقل |

اللعبة تقرأ نسخ PNG، والمصادر SVG قابلة للتعديل. شغّل tools/bake_sigil_assets.py بعد تعديل SVG.
الربط في assets/data/visual_defaults.json، ويظهر ضمن كتالوج العناصر في المحرر.
التحريك والشفافية والتدوير تظل برمجية؛ لم تتغير مدد المهارات أو الضرر.

## التصنيف والقرار

- إبقاء برمجي: تقدم الصحة/الخبرة/التبريد، الخريطة وخطوط اتصالها، حدود نطاق الإصابة الدقيقة، أدوات التطوير والتحديد، النصوص والتظليل العام للشاشة.
- احتياطي: جسم اللاعب والسلاح والمرافقون وبعض الأعداء عند غياب صورهم. وجود draw لا يعني ظهور شكل بدائي في التشغيل الطبيعي. لا نحذف مسارات الأمان عشوائيًا.
- يحتاج متابعة فنية: زخرفة موجة إيقاف الزمن وحوافها، بعض إشارات الهجوم والنطاقات، ومؤثرات فرعية في الحالات الخاصة. لم تُحوّل كل هذه العناصر في هذه الدفعة.
- هجين مقصود: صور المقذوفات والأشباح والانفجارات تتحرك وتتلاشى وتتمدد بالكود؛ هذا لا يجعلها رسومات مؤقتة.

## القائمة الكاملة لاستدعاءات pygame.draw داخل مجلدات التشغيل

هذه قائمة آلية بالمواقع، لا تصنيف مؤكد لظهورها. تُستثنى أدوات التطوير والاختبارات خارج مجلدات التشغيل. يمكن إعادة توليدها بعد كل تعديل.

| الملف | الدالة | الأسطر |
|---|---|---|
| game.py | draw_exit_portal | 377, 378, 379, 380, 381, 382, 383 |
| game.py | draw_movement_pickups | 471, 472, 473, 474, 463, 464 |
| entities/enemy.py | draw | 697 |
| entities/enemy.py | _draw_shadow_glow | 802, 811, 812, 846, 818, 848, 820, 823, 824, 826, 827 |
| entities/enemy.py | _draw_flash | 853 |
| entities/enemy.py | _draw_chaser | 872, 873, 874, 885, 886, 887, 878, 890 |
| entities/enemy.py | _draw_ranged | 940, 941, 948, 951, 956, 957, 960, 961, 962, 963 |
| entities/enemy.py | _draw_jumper | 1022, 1023, 1043, 1044, 1048, 1050, 1030, 1032, 1038 |
| entities/enemy.py | _draw_hunter | 1058, 1059, 1060, 1061, 1062, 1065 |
| entities/enemy.py | _draw_brute | 1076, 1077, 1078, 1079, 1080, 1081, 1083 |
| entities/enemy.py | _draw_elite | 1092, 1094, 1103, 1104, 1107, 1109, 1099, 1114 |
| entities/enemy.py | _draw_loot | 1124, 1125, 1126, 1127, 1128, 1129, 1130, 1134, 1135 |
| entities/enemy.py | _draw_boss | 1172, 1173, 1174, 1178, 1180, 1185, 1188, 1189, 1225, 1154, 1198, 1208, 1211, 1214, 1221, 1156, 1157, 1236, 1160 |
| entities/enemy.py | _draw_health_bar | 1248, 1249, 1256, 1257 |
| entities/enemy.py | _draw_vampire_wounds | 1268, 1269 |
| entities/enemy.py | _draw_windup_indicator | 1300 |
| entities/enemy_bullet.py | draw | 78, 84, 87, 91 |
| entities/enemy_bullet.py | draw | 153, 154, 139, 140, 141, 142 |
| entities/npc.py | _draw_tea_vendor | 112, 113, 114, 115 |
| entities/npc.py | _draw_blacksmith | 118, 120, 122, 123, 124, 125, 128, 129, 130 |
| entities/npc.py | _draw_healer | 133, 135, 138, 139, 141, 142, 147 |
| entities/npc.py | _draw_seer | 150, 152, 154, 155, 159, 160, 161, 167, 169 |
| entities/npc.py | _draw_generic | 172, 174, 176, 178, 179, 181, 182 |
| entities/pickup.py | draw | 171, 143, 147, 148, 149, 158, 159, 160, 164, 165, 166, 167 |
| entities/player.py | draw | 1126, 1128, 1132, 1136, 1140, 1151, 1162, 1163, 1168, 1177, 1181, 1185, 1186, 1189, 1120, 1195 |
| entities/player.py | _draw_sprite | 1237 |
| entities/player.py | _draw_engineer_drone | 1314, 1315, 1316, 1317, 1318, 1320 |
| entities/player.py | _draw_engineer_blades | 1345, 1338, 1339, 1340, 1341 |
| entities/player.py | _draw_engineer_bomber | 1374, 1380 |
| entities/player.py | _draw_blood_orb | 1398, 1399, 1400 |
| entities/player.py | _draw_blood_pickups | 1409, 1410, 1411 |
| entities/player.py | _draw_blood_bat | 1424, 1425, 1426, 1427 |
| entities/player.py | _draw_sprite_weapon | 1496, 1497 |
| entities/player.py | _draw_tea_item | 1519, 1520 |
| entities/projectile.py | draw | 115, 116, 117, 119, 122, 123, 125, 126, 127, 130, 134, 135, 136, 139, 140, 141 |
| systems/boss_encounter.py | draw_hud | 476, 482, 483, 485 |
| systems/boss_encounter.py | draw | 430, 431, 437, 439, 441, 460, 444, 470, 464, 452 |
| systems/crosshair_system.py | draw | 14, 23, 32 |
| systems/dev_tools.py | draw_debug | 1009, 1017, 1028, 1029, 1038, 1013, 1019, 1021, 1023, 1033 |
| systems/dev_tools.py | draw_selection_highlight | 1065, 1066 |
| systems/dev_tools.py | _draw_portals_and_exits | 1071, 1074 |
| systems/dialogue_system.py | draw | 49, 50 |
| systems/effects.py | draw | 63 |
| systems/effects.py | draw | 80, 81 |
| systems/effects.py | draw | 116, 117 |
| systems/environment_art.py | draw_cover | 87 |
| systems/hub_document.py | colliders | 31, 33 |
| systems/hub_presentation.py | draw_npc | 57 |
| systems/ninja_dash.py | draw_dash_sword | 52, 58, 57 |
| systems/object_catalog.py | draw_object | 278 |
| systems/pistol_presentation.py | render_pistol | 78, 80, 66 |
| systems/prototype_room.py | draw_stage_doors | 215, 223 |
| systems/prototype_room.py | draw_telegraphs | 245, 252 |
| systems/ranged_presentation.py | draw_cast | 56, 57, 58 |
| systems/ranged_presentation.py | draw_telegraph | 91, 103, 105, 108 |
| systems/room_layout.py | draw_room_obstacles | 58, 59, 60 |
| systems/room_layout.py | _draw_tiled_obstacle | 73 |
| systems/stage_system.py | draw_boss_gate | 373, 376 |
| systems/time_stop_presentation.py | layers | 15, 20 |
| systems/time_stop_presentation.py | draw | 55, 61, 62 |
| systems/world_utils.py | draw_world_background | 84, 140, 141, 100, 108, 119, 120, 124, 135 |
| ui/asset_browser.py | draw | 49 |
| ui/asset_browser.py | _draw_preview | 115, 116 |
| ui/asset_browser.py | _button | 248, 249 |
| ui/authoring_panel.py | _draw_panel | 159 |
| ui/authoring_panel.py | _draw_gizmos | 202, 204, 205, 210 |
| ui/authoring_panel.py | _draw_grid | 222, 224 |
| ui/authoring_panel.py | _draw_button | 243, 244 |
| ui/common.py | draw_bar | 43, 44, 45 |
| ui/cube_health.py | draw | 28 |
| ui/dev_panel.py | draw | 403 |
| ui/dev_panel.py | _draw_button | 436, 437 |
| ui/dev_panel.py | _draw_category_button | 445, 446 |
| ui/dev_panel.py | _draw_panel_box | 538 |
| ui/dev_panel.py | _draw_author_banner | 578 |
| ui/end_screen.py | draw_end_screen | 20, 33 |
| ui/front_end.py | backdrop | 52, 54 |
| ui/front_end.py | draw_button | 61, 62, 66, 64 |
| ui/front_end.py | draw_settings | 92, 96, 98, 99 |
| ui/front_end.py | draw_menu | 150 |
| ui/guidance.py | draw_guidance | 35, 18 |
| ui/hub.py | draw | 65, 66, 50, 77, 56 |
| ui/hud.py | _panel | 18, 19 |
| ui/hud.py | _bar | 25, 29, 28 |
| ui/hud.py | draw_hud | 198 |
| ui/minimap.py | draw_minimap | 21 |
| ui/minimap.py | _draw_stage_route | 73, 74, 89, 61, 72 |
| ui/minimap.py | _draw_stage_graph | 128, 127, 121 |
| ui/pause.py | _slider | 16, 26, 27, 28, 21 |
| ui/pause.py | draw_pause_menu | 45, 49, 57, 69 |
| ui/perk_screen.py | draw_perk_select | 76, 106, 113, 118, 120, 125, 143, 144, 235, 236, 135, 159, 167, 168, 174, 175, 186, 187 |
| ui/shop.py | draw_shop_hint | 28, 29, 60, 61 |
| ui/wave_designer_panel.py | draw | 35 |
| ui/wave_designer_panel.py | _draw_timeline | 67 |
| ui/wave_designer_panel.py | _button | 101, 102 |

# ActionRoguelike на daScript

Исходная версия: Tom Looman, ActionRoguelike, ветка UE5.6-CourseProject, коммит 992f860922373d50db05eacc5e1fce952ed88c13.

- Оригинал: https://github.com/tomlooman/ActionRoguelike
- Курс: https://tomlooman.com/courses/unrealengine-cpp/
- Локальная интеграция: C:/src/DasForUE2-main, Unreal Engine 5.8.3.

Вся игровая логика находится в daScript. C++ тест в репозитории DasForUE импортирует и проверяет классы; он не является реализацией игровой логики. Разрешение автора на публикацию и лицензия производного порта уточняются; MIT-лицензия DasForUE не переносится автоматически на этот пример. Ассеты курса сюда не скопированы.

## Первые классы

Content/Das/Scripts/rogue/rogue_interaction_interface.das объявляет настоящий UE Blueprint Interface с методом Interact без параметров.

Content/Das/Scripts/rogue/rogue_interaction.das вызывает этот интерфейс из daScript, отвергая пустые ссылки и объекты без нужного интерфейса.

Content/Das/Scripts/rogue/rogue_item_chest.das реализует RogueItemChest: два StaticMesh-компонента, редактируемые скорость и целевой pitch, включение tick при взаимодействии, равномерное вращение крышки и overridable событие ChestAnimationComplete. Начальный tick отключается в BeginPlay. Профили collision устанавливаются там же, после создания SCS компонентов; в C++ оригинале они задаются в конструкторе.

Поведение повторного взаимодействия сохранено: во время анимации оно не сбрасывает прогресс; после полного открытия повторно вызывает завершение на следующем tick. Нулевая скорость не завершает движение к отличающейся цели. Событие завершения в базовом классе имеет пустую реализацию и может быть переопределено в дочернем Blueprint.

В текущем DSL изменяемое состояние CurrentAnimationPitch хранится как отражаемое BlueprintReadWrite поле. В оригинале это обычное C++ поле; оно не является настраиваемым параметром анимации порта.

## Импорт в редакторе

Проект подключает локальный плагин через AdditionalPluginDirectories. Для открытия нужен собранный совместимый DasForUE; сборки Unreal запускать через общий агент репозитория, как описано в его Docs/Dev/Testing.md.

В консоли редактора последовательно выполнить:

```text
Das.DSL.Interfaces.Apply rogue_interaction_interface.das /Game/DasRogue/Types
Das.DSL.Apply rogue_item_chest.das /Game/DasRogue/BP_RogueItemChest rogue.RogueItemChest
```

Сохранить созданные assets. Разместить сундук на карте, назначить BaseMeshComponent и LidMeshComponent свои mesh-ресурсы с подходящим pivot крышки. Вызвать Interact через интерфейс из Blueprint. Имя и путь интерфейса пока фиксированы в объявлении класса и должны совпадать с командой импорта.

## Проверка

Целевой suite rogue-chest добавлен в C:/src/DasForUE2-main/Tests/suites.json. Через общий агент C:/src/DasForUE2 отправить строку:

```text
test-suite rogue-chest-local rogue-chest repo=C:/src/DasForUE2-main
```

Тестовый runner копирует три исходника и Tests/Das/roguetest/rogue_item_chest_observer.das в Content/Das/Scripts smoke-проекта. Канонические исходники находятся здесь. Автотест DasForUE.Ports.RogueChest проверяет интерфейс, компоненты, tick, углы, повторное взаимодействие и две независимые копии. Результаты и ограничения запуска фиксируются в VALIDATION.md после проверки.

## Выбор цели и клавиша E

Первый этап реализован полностью: `rogue_interaction_component.das` принадлежит контроллеру и каждый tick выбирает объект в радиусе 800 по весу расстояния и направления камеры. `rogue_player_controller.das` создаёт этот компонент, устанавливает TeamId=1 и подключает Enhanced Input после готовности локального ввода. Вся игровая логика находится в daScript.

В `Content/Das/Scripts/rogue/rogue_player_controller.das` заданы ссылки по умолчанию на `/Game/DasRogue/Input/IA_Interact` и `IMC_Rogue`. Эти ресурсы создаёт `Scripts/prepare_interaction.py` до импорта класса. Mapping связывает E с Boolean action; событие Started вызывает взаимодействие один раз за нажатие. Удержание E не вызывает повторных команд. Это осознанное отличие от Triggered в исходном контроллере.

Компонент отбрасывает объекты без интерфейса, безопасно обрабатывает отсутствие pawn и обновляет выбор непосредственно перед вызовом Interact. Автоматический таймер открытия удалён. На карте используется `RogueInteractiveChest`, наследующий только поведение сундука.

Для проверки открыть `ActionRoguelikeDas.uproject`, карту `/Game/DasRogue/Maps/ChestTest`, нажать Play, щёлкнуть в игровой viewport и нажать E. Сундук открывается за 2,4 секунды. Камера PlayerStart уже находится в радиусе взаимодействия и смотрит на сундук. Персонаж BP_RogueCharacter реализован на daScript: WASD, мышь и Space; камера от третьего лица через SpringArm.

Подготовка карты выполняется редакторским Python-скриптом `Scripts/prepare_interaction.py`: создаёт input assets, импортирует классы, назначает daScript-контроллер через GameMode и заменяет прежний автоматический demo actor. Скрипт использует простые engine cube meshes; ассеты курса не требуются.

Suite `rogue-interaction` проверяет настоящий PIE и ввод E через PlayerController.InputKey, выбор двух сундуков, удержание клавиши, выход из радиуса, удаление цели, отсутствие pawn и очистку runtime после EndPIE. Команда агенту: `test-suite rogue-input-local rogue-interaction repo=C:/src/DasForUE2-main`.


## RogueProjectile и ЛКМ

`rogue_projectile.das` переносит базовый ARogueProjectile из зафиксированной версии курса: SphereComponent радиусом 16, ProjectileMovement со скоростью 2000 и нулевой гравитацией, LoopedNiagaraComponent и LoopedAudioComponent, срок жизни 30 секунд, исключение Instigator из swept collision, OnComponentHit → разовые эффекты → Destroy. Урона в этом базовом классе нет, как и в оригинале. HasImpacted защищает от повторной обработки попадания.

`rogue_projectile_demo.das` добавляет видимую сферу из Engine/BasicShapes и отключает её собственную коллизию. Авторские ассеты курса не используются. Базовые ExplosionSound/ExplosionEffect опциональны. Демонстрационный потомок назначает engine sound 1kSineTonePing и Niagara template RadialBurst; их можно заменить своими ресурсами. Зацикленные эффекты по умолчанию пусты.

Текущий `RoguePlayerController` привязывает Boolean `IA_Fire` к Triggered для ЛКМ. Он запрашивает Action.PrimaryAttack у компонента персонажа. RogueActionProjectileAttack выдерживает задержку каста и создаёт экземпляр ProjectileClass с Owner=controller и Instigator=pawn. Удержание ЛКМ повторяет атаку с учётом cooldown. Поведение стрельбы написано на daScript. E продолжает открывать сундук.

Подготовка карты: редакторский `Scripts/prepare_projectile.py` создаёт input assets, импортирует классы и добавляет стену для попаданий. Он использует общую настройку `prepare_interaction.py`. В PIE щёлкнуть viewport для захвата мыши, затем ЛКМ стреляет по направлению камеры. Одно нажатие даёт один снаряд.

Скорость, гравитация, радиус и эффекты настраиваются на скриптовом классе. Native-компоненты создаются через SCS; runtime-настройка выполняется в BeginPlay после регистрации компонентов, вместо C++ конструктора/PostInitializeComponents. Базовый класс доступен для создания в редакторе (исходный C++ класс Abstract); демонстрация использует его дочерний класс.


## Управление через Unreal MCP

Установлен ATDev UEMCP в C:/src/unreal-mcp (исходный commit 3d38a7b2067275d9d0df7f932775204958a0e5a9, локальная .venv). В Codex зарегистрирован включённый stdio server `unreal`, executable C:/src/unreal-mcp/.venv/Scripts/uemcp.exe; UEMCP_PROJECT=ActionRoguelikeDas, UEMCP_MULTICAST_BIND=127.0.0.1.

PythonScriptPlugin уже включён в .uproject. DefaultEngine.ini содержит постоянный bRemoteExecution=True, bind=127.0.0.1, multicast=239.0.0.1:6766, TTL=0. Эти настройки применяются при каждом открытии проекта. Ручной запуск отдельного сервера не требуется: stdio-процесс запускает MCP-клиент Codex.

В UE 5.8 get_editor_subsystem(LevelEditorSubsystem) в этой сборке возвращает None. В локальном UEMCP добавлен fallback к CDO для статeless глобальных LevelEditor Play/Stop commands. Для настоящего PIE через ue_python вызывается `(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)).editor_request_begin_play()`. Стандартный ue_play у UEMCP запускает Simulate, а не управление игровым персонажем.

Если в уже открытом чате Codex новые инструменты не появились, требуется новый сеанс клиента: конфигурация MCP сохраняется глобально. Протокол и команды проверены локальным MCP SDK без computer-use.


## Здоровье и магический снаряд

На ChestTest добавлена зелёная мишень справа от сундука с надписью `HP: 100 / 100`.
ЛКМ теперь создаёт `BP_MagicProjectileDemo`: каждое попадание снимает 25 HP,
мишень постепенно краснеет и исчезает после четвёртого попадания. E открывает
сундук с шарниром у заднего края. Новый Play восстанавливает мишень.

Скорость: Content Drawer → Content → DasRogue → BP_MagicProjectileDemo →
Class Defaults → Projectile → Initial Speed. Урон там же: Attack Damage.
Исходный BP_ProjectileDemo сохранён как отдельный пример без урона, включая
настроенную пользователем скорость 250 см/с. У нового магического снаряда
скорость по умолчанию 2000 см/с, lifetime 8 секунд.

Код: rogue_attribute_component.das (HP, clamp, изменение здоровья и native
OnTakeAnyDamage), rogue_attribute_events.das (OnHealthChanged),
rogue_magic_projectile.das (урон), rogue_target_dummy.das (индикация и смерть).
Событие попадания расширяется через RogueImpactHandler, а не второй подпиской
на OnComponentHit. Геометрия, текст и материал — собственный тестовый контент.

Подготовка в открытой карте редактора: Scripts/prepare_health.py. Перед этим
базовую карту/ввод создают prepare_editor.py и prepare_projectile.py.
Проверка в свежем PIE: Tests/verify_health_pie.py; результат —
Saved/Tests/rogue_health_pie.json. Тест сам наводит камеру, проверяет clamp,
лечение/no-op и выполняет четыре отдельных выстрела через Enhanced Input.

Это первый срез системы урона. PointDamage, импульс физическим объектам,
AI noise, action effects, сетевое состояние и полноценный персонаж следуют
отдельными этапами. Оптимизация компиляции/создания VM ведётся отдельно.


## Персонаж: движение и камера

Content/Das/Scripts/rogue/rogue_character.das переносит движение, взгляд и прыжок
RoguePlayerCharacter. GameMode использует BP_RogueCharacter вместо DefaultPawn.
W/S — вперёд/назад относительно yaw камеры, A/D — влево/вправо, мышь — обзор,
Space — прыжок; отпускание Space вызывает StopJumping. E и ЛКМ остаются
в daScript контроллере. Камера прикреплена к SpringEndpoint у SpringArm длиной
175 см, высотой 80 см и плечевым смещением Y=80; корпус следует yaw камеры. Cone — временная
геометрия из стандартных ресурсов движка, без collision; движение использует
нативную капсулу Character. Локальные mesh/анимации подключаются через presentation profile.

WalkSpeed=550, JumpVelocity=420, AirControl=0.05 редактируются в Class Defaults
BP_RogueCharacter и применяются скриптом в BeginPlay. Состояние ControlsBound
и счётчики событий доступны для диагностики. Подключены Attributes и первый
срез смерти игрока и система действий. Снаряд
запускается от персонажа, а камера выбирает точку прицеливания.

Scripts/prepare_character.py создаёт IA_Move, IA_Look, IA_Jump и IMC_Character,
импортирует персонажа и задаёт DefaultPawnClass текущего GameMode. Запускать
после подготовки взаимодействия/здоровья, вне PIE, через Unreal Python.
Модификаторы ключей сохраняются явной записью DefaultKeyMappings.Mappings: UE
Python map_key возвращает копию структуры; изменение только возвращённого
entry не сохраняет Negate/Swizzle в mapping asset.

Tests/verify_character_pie.py запускать в свежем PIE ChestTest через Unreal
Python. Тест использует Enhanced Input с сохранёнными модификаторами клавиш,
проверяет реальное перемещение, камеру, прыжок, сундук и попадание в мишень.
Результат: Saved/Tests/rogue_character_pie.json. Во время теста не вводить
управление вручную. После теста перезапустить PIE для обычной проверки.


## Стрельба от персонажа, здоровье и смерть

Действие RogueActionProjectileAttack вычисляет точку прицеливания через Visibility line trace из камеры,
игнорируя своего pawn. MuzzleOffset=75 см по горизонтальному направлению камеры,
MuzzleHeight=40 см от позиции pawn; AimDistance=10000 см. Направление снаряда —
от этой точки к первому попаданию луча либо его дальней точке при промахе.
Все расчёты — daScript. Owner/Instigator задаются перед BeginPlay снаряда.
MuzzleClearance=16 см проверяет путь от верхней точки персонажа до muzzle
через sphere trace. У стены muzzle остаётся с ближней стороны; если исходная
сфера уже внутри препятствия или цель позади muzzle, выстрел отклоняется.
LastMuzzleLocation/LastAimPoint/BlockedShots находятся в экземпляре действия (ActionSystem.Actions) во время PIE.
При смене радиуса снаряда согласовать MuzzleClearance с его CollisionRadius.

На BP_RogueCharacter установлен готовый RogueAttributeComponent (100 HP).
Текст над персонажем показывает HP и поворачивается к камере. Клавиша H —
проверочный урон TestDamage=25 через обычный native OnTakeAnyDamage. Четыре
отдельных нажатия приводят к смерти: Dead=true, DeathCount=1, остановка и
DisableMovement, DisableInput персонажа и контроллера, блокировка move/look.
Текст меняется на DEAD. Для повторной проверки остановить и заново запустить
Play. Локальный профиль игрока добавляет death montage; respawn ещё не перенесён.
Из-за временной геометрии без SkeletalMesh капсула блокирует Projectile; свой
снаряд продолжает игнорировать Instigator.

Подготовка: Scripts/prepare_character.py (после этапа здоровья). Дополнительный
тест: вне PIE выполнить Scripts/prepare_combat_test.py, затем начать свежий PIE
и выполнить Tests/verify_character_combat_pie.py. Стенд CombatProbe только
создаёт тестовые акторы через обычный daScript spawn; в нём нет боевой логики.
После теста удалить BP_CombatProbe из editor world; в обычной карте его нет.
Результат: Saved/Tests/rogue_character_combat_pie.json.

## Система действий и Sprint

Первый срез системы действий перенесён на daScript: RogueAction,
RogueActionSystemComponent и RogueActionSprint. Удерживайте Left Shift при
движении: MaxWalkSpeed меняется с 550 на 880 (SpeedMultiplier=1.6). Отпускание
Shift возвращает исходную скорость. StatusEffect.Stunned блокирует и отменяет
Sprint; смерть останавливает действия и запрещает повторный запуск.

На BP_RogueCharacter настройка SprintActionClass выбирает класс действия.
Персонаж выдаёт его компоненту в BeginPlay через daScript. DefaultActions
компонента остаётся доступен для других наборов способностей. Старое назначение
Sprint через Python CDO заменено настройкой в rogue_character.das. Настройка
SpeedMultiplier находится в Class Defaults BP_RogueActionSprint, раздел Sprint.

Объекты действий принадлежат компоненту через отражённый массив Actions. Outer
задаёт контекст/мир, а сильные ссылки массива обеспечивают время жизни. У каждого
персонажа свои экземпляры. Фабрика принимает наследника базового RogueActionRef,
но отклоняет чужую authored-иерархию до создания экземпляра.

Автоматическая проверка запускается общим build-agent: suite `rogue-actions`.
Она сама готовит проект, запускает PIE, проверяет GC, фабрику, двух владельцев,
стоимость/cooldown, Shift, оглушение и смерть, затем удаляет тестовый актор и
закрывает редактор. Результат: Saved/Tests/rogue_actions_pie.json; подробный лог
в DasForUE2-main/logs/rogue-actions.log. Ручное переключение MCP не требуется.
Следующий срез — action effects и модификаторы; стрельба уже принадлежит RogueActionProjectileAttack.


## Projectile attack action

ЛКМ запускает `Action.PrimaryAttack`. `RogueActionProjectileAttack` начинает каст,
через `AttackDelay=0.2` секунды создаёт снаряд и завершает действие. Затем действует
`CooldownTime=0.5` секунды. Повторный запуск во время каста/cooldown отклоняется;
удержание ЛКМ даёт один Started. Оглушение, удаление действия и смерть отменяют таймер.
Игровая логика и таймер принадлежат daScript ScriptObject, который удерживает
отражённый массив `RogueActionSystemComponent.Actions`.

Настройки находятся в `Content/DasRogue/Actions/BP_RogueActionProjectileAttack`,
`Class Defaults → Attack`: ProjectileClass, AttackDelay, AttackMontage,
CastingEffect, CastingSound, MuzzleSocketName и параметры запасного muzzle.
CooldownTime унаследован из раздела Actions. Скорость полёта по-прежнему задаётся
в классе самого снаряда, а не в действии или контроллере.

Если у SkeletalMesh есть `Muzzle_01`, выстрел использует этот сокет. Для конуса без
скелетного ресурса остаётся muzzle от pawn (75 см вперёд, 40 см вверх). Сохранены
прицеливание трассировкой от камеры на 10000 см и проверка близкого укрытия.
AttackMontage, CastingEffect и CastingSound необязательны. Niagara прикрепляется
к компоненту/сокету с auto-destroy, звук каста запускается в 2D. На текущем конусе
нет скелетного меша/AnimBP, поэтому без локального профиля montage не виден.
С установленным профилем курса используются Manny и его AnimGraph (см. ниже).

Автопроверка: suite `rogue-projectile-attack`, результат
`Saved/Tests/rogue_projectile_attack_pie.json`. Подготовка мигрирует старый контроллер
через `fields=archive_remove_with_dependencies`; удалённые поля архивируются.
Повторная подготовка использует обычный Reimport.


## Локальное представление из ресурсов курса

Пример поддерживает Manny Simple с анимациями Gideon, монтажем атаки и локальными
Niagara/звуками курса. Установщик, источники и условия описаны в EXTERNAL_ASSETS.md.
Внешние файлы и сгенерированный профиль в Git не входят. Без профиля остаётся
простая геометрия; UseExternalPresentation и PresentationProfilePath находятся
в настройках персонажа. Gameplay остаётся в daScript, AnimGraph отвечает за позу.


## Action effects — первый срез

`RogueActionEffect` наследует действие: `Duration` задаёт время жизни (0 — до
явной остановки), `Period` — интервал вызова `ExecutePeriodicEffect` (0 — без
периодических вызовов). Выдача через `ActionSystem.GrantAction` автоматически
запускает эффект. Повторная выдача того же конкретного класса увеличивает
`StackCount`; `ResetDurationOnStackIncrease` управляет обновлением срока.

Эффект сам удаляется при остановке. Компонент хранит сильную отражённую ссылку
до удаления, а таймеры отменяются при остановке, Shutdown и EndPlay. Удаление
из компонента выполняется перед callback остановки, чтобы не вызывать рекурсию;
массовая остановка использует копию списка, поскольку эффекты удаляют себя.

`RogueActionEffectStun` выдаёт `StatusEffect.Stunned` на 2.5 секунды. Это отменяет
Sprint/основную атаку и блокирует их до истечения эффекта. Класс находится в
`/Game/DasRogue/Actions/BP_RogueActionEffectStun`. Он не выдаётся игроку при старте:
боевой код должен применить его через GrantAction.

`RoguePeriodicEffect` — проверочный наследник, увеличивающий Rage пропорционально
стеку. Он находится в Tests/Das, а не в настройках игрового персонажа. Overwhelm
и связь с попаданиями описаны ниже; остальные боевые эффекты остаются впереди.

## Overwhelm и эффекты попадания

На ChestTest добавлена отдельная мишень `daScript Combat Target - Overwhelm`
слева от сундука. Обычная мишень с четырьмя попаданиями остаётся на карте.
У боевой мишени есть ActionSystem и постоянно активный RogueActionEffectOverwhelm.
Он суммирует урон между соседними попаданиями, если прошло меньше одной секунды;
по умолчанию порог равен 20. При стандартном уроне снаряда 25 stun срабатывает
с первого попадания. Надпись STUNNED исчезает через 2.5 секунды. Урон во время
stun не накапливается для следующего оглушения и не продлевает его через Overwhelm.

Для настройки откройте Content/DasRogue/Actions/BP_RogueActionEffectOverwhelm,
Class Defaults, раздел Overwhelm: DamageThreshold, TimeDeltaThreshold и
EffectOnThreshold. Например, порог 50 требует двух стандартных попаданий в окне.
Это окно между соседними событиями урона, как в исходнике, а не фиксированное
окно от самого первого попадания. Лечение не сбрасывает и не увеличивает сумму.

Отдельно в Content/DasRogue/BP_MagicProjectileDemo → Class Defaults → Projectile
есть унаследованный EffectOnHit. По умолчанию он пуст: можно выбрать, например,
BP_RogueActionEffectStun. Такой эффект применяется при каждом попадании и может
увеличивать стек/обновлять длительность; он не использует ограничения Overwhelm.
Неподходящий класс действия отклоняется до создания объекта. Эффект работает
и при нулевом AttackDamage. Если у цели нет ActionSystem, остаётся обычный урон.

Overwhelm отписывается от здоровья при остановке и удалении. Мишень использует
управляемые ue_event для обновления статуса; при смерти ActionSystem выключается
и очищает эффекты. Расчёт cooldown при Shutdown/EndPlay не требует времени
уничтожаемого мира.

## Точечный урон и физические попадания

Снаряд передаёт полный `CollisionHit` через `RogueImpactHandler`. MagicProjectile
вызывает UE ApplyPointDamage с направлением полёта, компонентом и костью попадания;
AttributeComponent продолжает получать одно событие общего урона. Повторные
коллизии отсекает базовый снаряд. EffectOnHit и Overwhelm работают после этого урона.

В Class Defaults `/Game/DasRogue/BP_MagicProjectileDemo`, раздел Projectile:
- `AttackDamage` — урон (25 по умолчанию).
- `ImpulseIntensity` — импульс физическому телу (200000, 0 выключает).
- `NoiseLoudness` — громкость события AI hearing (1, 0 выключает).
- `InitialSpeed` — скорость в см/с (2000).

На ChestTest есть куб `Physics target - shoot with LMB`: выстрел должен сдвигать
его. Импульс применяется только при IsSimulatingPhysics для кости попадания.
Событие шума содержит Instigator снаряда; на карте есть AI-противник
со слухом и зрением.

Сохранённые Blueprint и исходники используют новый контракт попадания вместе.
При разовом обновлении старых ресурсов настройки родителя и дочернего снаряда
применены отдельно перед совместной миграцией интерфейса и реализаций.

## AI-противник — первый боевой срез

Добавлены `rogue_ai_character.das`, `rogue_ai_controller.das` и
`rogue_ai_projectile_attack.das`. Вся логика выбора цели, преследования, запроса
действия, stun и смерти находится в daScript. Native AIPerception создаёт события
зрения, слуха и урона; generic API DasForUE настраивает senses и предоставляет focus/LOS.
Поведение соответствует первому боевому срезу RogueAICharacter/Controller и
RogueBTTask_RangedAttack оригинала. Полное дерево перенесено отдельным контроллером
RogueBehaviorController; описание — ниже.
Лечение, добыча и патруль описаны ниже.

`Scripts/prepare_ai.py` создаёт Blueprint-ассеты в `/Game/DasRogue/AI`, связывает
AIControllerClass/AutoPossessAI и добавляет противника и открытый пол на ChestTest.
Эта Python-настройка работает только в редакторе; игровое поведение она не реализует.
Противник стоит около `(3000, 800, 96)`, игрок начинает у сундука. После
сборки/подготовки карты: Play, подойти к противнику, стрелять ЛКМ. Два обычных
попадания по 51 урона убивают противника с базовыми 100 HP.

Настройки контроллера: SightRadius, LoseSightRadius, SightAngle, HearingRadius,
TargetMemory, AttackRange, ThinkInterval. `UsePathfinding=false` использует
прямой native MoveTo в открытой арене; обход препятствий требует построенного
NavMesh и `UsePathfinding=true`. Это ограничение первого среза.

Игрок сохраняет прицеливание по камере. AI-способность переопределяет GetAimPoint
и GetAimRotation для выбранного Actor, затем добавляет разброс в GetProjectileRotation;
у снаряда общий ControllerRef, поэтому
AI-инстигатор корректно проходит через point damage.

Регрессия `rogue-ai` использует реальный PIE: sight/hearing, движение, попадание
в игрока, stun, LOS/истечение памяти и смерть. Результаты проверок записываются в `Saved/Tests/`.

## Ссылки по стабильному ID

Пример использует `UEObjectRef("rogue.RogueAction")` и `UEInterfaceRef("rogue.RogueActionHost")` без имён файлов. В `DefaultEngine.ini` включено `[DasForUE.SourceCatalog] AutoGenerate=True`: редактор обновляет `Content/Das/Scripts/ue_type_catalog.json` по объявлениям классов, интерфейсов, структур и перечислений до компиляции. Каталог не нужно редактировать вручную. При явном `module_id` или `id` переименование файла сохраняет ID. Для commandlet/cook используйте актуальный сгенерированный каталог; его можно обновить открытием проекта в редакторе. Каталог не создаёт ресурсы интерфейсов и типов — они проходят обычный импорт и проверку.

Типы ссылок объявлены через `typedef` рядом с соответствующим классом или интерфейсом, например `RogueActionRef` в `rogue_action.das`. Отдельных `*_refs.das` больше нет; потребители импортируют модуль владельца. Тестовые исходники используют те же импорты.

## Организация скриптов

- `Content/Das/Scripts/rogue/` — игровая логика, компоненты, действия, интерфейсы и presentation.
- `Content/Das/Scripts/roguedemo/` — конкретные объекты демонстрационной сцены: сундуки, снаряды, мишени.
- `Content/Das/Scripts/roguetest/` — проверочные классы; исходные заготовки тестовых сценариев находятся в `Tests/Das/roguetest/`.

Папки соответствуют группам стабильных ID `module_id`; отдельные daScript-модули сохраняют имена (`rogue_character`, `rogue_action` и т. п.). Импорты и ID типов не меняются при переносе. Индекс имён файлов строится при старте загрузчика и обновляется при сообщении об изменении состава файлов; обычный поиск использует таблицу в памяти. Одинаковые имена файлов в разных проектных папках отклоняются как неоднозначные. Генерируемый `ue_type_catalog.json` остаётся в корне `Scripts` и хранит относительные пути с папками.

`RogueSkeletalMeshRef` объявлен рядом с профилем через `UENativeObjectRef`; отдельного `rogue_presentation_types.das` больше нет.

## Внешний вид AI Minion

Необязательный локальный профиль Paragon Minions добавляет модель, движение,
подготовку атаки и stun. Попадание включает общий overlay; смерть использует ragdoll. Установка и генерация
описаны в [EXTERNAL_ASSETS.md](EXTERNAL_ASSETS.md#paragon-minion).
В `BP_RogueAICharacter`, Class Defaults → AI, доступны `UseExternalPresentation`
и `PresentationProfilePath`. Отсутствующий профиль сохраняет базовый конус.
Публичные Blueprint не хранят жёстких ссылок на внешние ресурсы.

Для ручной проверки откройте ChestTest, нажмите Play и подойдите к арене около
`(3000, 800)`. Миньон преследует игрока и готовит выстрел; попадание ЛКМ включает
вспышку, сохраняя подготовку атаки. Проверка `rogue-ai-presentation` проверяет изменение
позы, сокет оружия, восстановление после stun, кадр вспышки и ragdoll на 10 секунд.


## Патруль на NavMesh

Откройте `Content/DasRogue/Maps/PatrolTest` и нажмите Play. В арене около
`(3200, 0)` Minion ходит между четырьмя точками, обходит центральное препятствие,
переключается на бой при обнаружении игрока и возвращается к маршруту после
потери цели. На этой карте используется `BP_RoguePatrolController`; ChestTest
сохраняет прежний сценарий. Все решения выполняются в daScript.

В Outliner точки названы `Patrol point A`–`D`; их `MaxPathLength` ограничивает
длину native navigation corridor, а не расстояние по прямой. При нескольких
выходах предыдущая точка исключается из выбора. В Class Defaults контроллера
группа Patrol задаёт `PatrolWait`, `PatrolRetryDelay`, `PatrolAcceptanceRadius`
и `PatrolEnabled`. Граф строится после готовности NavMesh; после изменения
набора точек в игре можно вызвать `RefreshPatrolGraph`.

Для повторной подготовки карты выполните в редакторе Python:
`py __import__('runpy').run_path(r'C:/src/ActionRoguelikeDas/Scripts/prepare_patrol.py')`.
Этот скрипт ожидает уже подготовленные общие игровые ассеты. Он настраивает карту,
а игровая логика находится в `rogue_patrol_point.das` и `rogue_patrol_controller.das`.
Проверка `rogue-patrol` прошла девять групп в реальном PIE; результат записывается
в `Saved/Tests/rogue_patrol_pie.json`.


## Лечебный pickup

На `ChestTest` возле `(300, -250, 80)` стоит зелёная сфера. В Outliner она
называется `Health pickup - press E - respawns in 5 seconds`.
Нажмите Play, получите урон клавишей **H**, подойдите к сфере на расстояние
до 250 см и нажмите **E**. Предмет лечит на 50 HP с ограничением HealthMax,
исчезает и становится доступен через 5 секунд. При полном здоровье он остаётся
на месте. `HealingAmount`, `PickupSound`, `RespawnDelay` и дистанция настраиваются
в Details / Class Defaults соответствующего Blueprint.

Три класса находятся в `Content/DasRogue/Pickups`:

- `BP_RoguePickupActor` — основа подбора и жизненного цикла.
- `BP_RogueHealthPickup` — исходный режим: пересечение с Pawn, лечение,
  одноразовое удаление. По умолчанию RequireInteraction=false, RespawnDelay=0.
- `BP_HealthPickupInteract` — явный демонстрационный вариант с E и respawn.

В зафиксированной версии курса используется overlap и Destroy, а не E и таймер.
Эти режимы разделены настройками и классом из `roguedemo`. Интерфейс Interact
не передаёт пользователя, поэтому демонстрационный вариант берёт local player 0.
Текущее лечение использует существующий RogueAttributeComponent; полная модель
атрибутов ActionSystem остаётся отдельным этапом. Погибшие Pawn и неположительное
лечение не потребляют предмет. Звук необязателен; оформление использует engine mesh.

Подготовка ассетов и размещение выполняются `Scripts/prepare_health_pickup.py`
после общей подготовки персонажа. Всё поведение находится в daScript; Python
не выполняет игровое лечение или respawn. Suite `rogue-pickup` проверяет восемь
групп в настоящем PIE, включая Enhanced Input, native overlap и уничтожение
предмета с ожидающим таймером. Отчёт: `Saved/Tests/rogue_pickup_pie.json`.


## Монеты и DropLoot

На `PatrolTest` после смерти врага появляются золотые диски. Подойдите к ним:
монеты в радиусе 200 см собираются, а баланс `Coins` обновляется в HUD.
Один мировой `RogueCoinPickupSubsystem` хранит все монеты в общем ISM без
отдельного Actor на каждый диск. Монеты остаются после исчезновения тела.

`DropLootActionClass` врага задаёт действие выдачи награды; `MonsterData.LootCoins`
задаёт сумму. Без данных выпадает 10 кредитов. `MaxCreditsPerCoin` по умолчанию 15;
при недоступном NavMesh вся награда остаётся у позиции погибшего врага.
В `Content/DasRogue/Pickups/BP_RogueCoinPickupSubsystem`, Class Defaults → Coins,
настраиваются радиус подбора, mesh, material и необязательный звук.
`BP_RogueCoinTestActor` позволяет задать `InitialCoinCount` для демонстрационной
партии; на тестовой карте он изначально равен нулю.

Кошелёк, суммарная стоимость монет и `OnCoinsChanged` используют `int64`.
Начисления проверяются на отрицательные значения и переполнение; HUD выводит
баланс без преобразования к float или int32. Аудит типов — в `BINDING_AUDIT.md`.
Suite `rogue-coins` проверяет реальные Tick, сбор, GC, DropLoot и очистку PIE.
Отчёт: `Saved/Tests/rogue_coins_pie.json`. Подготовка ассетов и карты:
`Scripts/prepare_coins_test.py`; вся игровая логика выполняется в daScript.


## AttributeSet и Rage

Health, HealthMax, MoveSpeed и MoveSpeedMultiplier теперь хранятся в общем
RogueAttributeSet с Base/Modifier. У игрока дополнительно есть Rage; у монстров
этого атрибута нет. Изменения передаются событиями в компоненты и UI.

Для ручной проверки на ChestTest нажать H: при стандартном TestDamage=25 здоровье
уменьшится на 25, Rage увеличится на 18.75. Значение Rage показано рядом с HP и Coins.
Подбор лечения восстанавливает HP и не даёт Rage. Shift по-прежнему включает спринт.
Классы наборов доступны в Content/DasRogue/Attributes; игровая реализация —
Content/Das/Scripts/rogue/rogue_attribute_set.das.

Проверка нового среза через общий агент:

```text
test-suite rogue-attributes-local rogue-attributes repo=C:/src/DasForUE2-main
```


## Взрывающаяся бочка

Откройте `Content/DasRogue/Maps/BarrelTest` и нажмите Play. Перед игроком стоит
`Explosive barrel - shoot once - 3 second fuse`. Наведитесь на цилиндр и стреляйте
ЛКМ: попадание запускает трёхсекундный фитиль. Близкий куб получает физический
импульс, дальний находится вне радиуса. Сама бочка подбрасывается и вращается.
Взрыв не наносит radial damage и не удаляет бочку — это поведение исходника.

`BP_RogueExplosiveBarrel` находится в `Content/DasRogue/World`. В Details доступны
`ExplosionDelay`, необязательные Niagara/audio для горения и взрыва. На компоненте
`RadialForceComponent` задаются `Radius` (750 см) и `ImpulseStrength` (150000).
Пока эффекты не назначены, демонстрация использует engine cylinder и кубы.
Гравитация тестовых кубов отключена для воспроизводимой проверки дальности.

Повторные попадания не продлевают фитиль. Повторный вызов `Explode` не создаёт
новый импульс; прямой вызов во время горения отменяет ожидающий таймер.
Некорректная неположительная/нечисловая задержка не запускает горение.
`Scripts/prepare_barrels.py` повторно собирает арену; игровое поведение находится
в `rogue/rogue_explosive_barrel.das`. Suite `rogue-barrels` проверяет восемь групп
в реальном PIE, отчёт — `Saved/Tests/rogue_barrels_pie.json`.


## Blackhole

Откройте `Content/DasRogue/Maps/BlackholeTest` и нажмите Play. Видимая тёмная сфера
перед игроком притягивает два физических куба и поглощает их при достижении ядра.
Через 5 секунд сфера исчезает. Повторный Play восстанавливает демонстрацию.
У кубов включён Generate Overlap Events; без него поглощение не происходит.

`Content/DasRogue/Projectiles/BP_RogueProjectileBlackhole` — основной снаряд:
500 см/с, lifespan 5 секунд, ядро 20 см, ForceStrength=-800000 и Radius=1200 см.
Он проходит сквозь стены и не вызывает базовый взрыв при попадании. Pawn исключён
из radial force. Ядро с профилем BlackholeCore пересекается только с PhysicsBody
и удаляет актор при условии IsSimulatingPhysics у пересёкшего компонента.
В `BP_BlackholeDemo` скорость намеренно равна нулю и добавлен видимый engine mesh;
это отдельное оформление из roguedemo, а не изменение скорости основного класса.

Для выстрела используется BP_BlackholeAttackProjectile: он сохраняет движение
основного класса и добавляет локальное оформление. BP_BlackholeDemo остаётся
неподвижным примером для арены. Подготовка арены: `Scripts/prepare_blackhole.py`.
Suite `rogue-blackhole` проверяет восемь групп настоящего PIE, включая регрессию
обычного снаряда; отчёт — `Saved/Tests/rogue_blackhole_pie.json`.


## Движение как в оригинальном Blueprint

Корпус следует yaw камеры. A/D дают стрейф, S — движение назад с сохранением
направления корпуса. Базовая скорость 550; существующий спринт даёт 880.
Камера использует исходные настройки BP_PlayerCharacter: arm 175, высота 80,
плечевое смещение Y=80. JumpZVelocity=420, AirControl=0.05.
Настройки сверены с реальным Blueprint оригинала 992f860, а не только с C++ defaults.

Через общий агент: `test-suite rogue-movement-local rogue-movement repo=C:/src/DasForUE2-main`.
Проверка читает оригинальный проект в C:/src/ActionRoguelike и затем проверяет
движение, направление корпуса, скорость, торможение и спринт в реальном PIE.


## Боевой паритет с оригиналом

Основной magic projectile наносит 51 урона; игрок движется со скоростью 550,
AI — 450. Свой снаряд и движение его владельца игнорируют друг друга.
AI воспринимает Damage наряду со Sight/Hearing, исключая friendly damage stimuli.
Разброс MaxBulletSpread=5 задаёт pitch [0,5] и yaw [-5,5] от фактической точки вылета.

Игрок и AI используют RogueHitFlashComponent: CustomPrimitiveData[0] хранит время
попадания, overlay отключается через секунду после последнего удара. Генератор
Scripts/prepare_hit_flash.py создаёт наш материал M_HitFlash, без внешних ресурсов.
Урон AI не отменяет готовящийся выстрел. После смерти Minion использует свой PhysicsAsset
и Ragdoll на 10 секунд; для skeletal ragdoll нужны установленные локальные ресурсы.

Suite: `test-suite combat-parity-local rogue-combat-parity repo=C:/src/DasForUE2-main`.
Временное project-local отключение дискового кэша компиляции описано в MODULE_CACHE_REPRO.md.

## Дополнительные атаки

`Scripts/prepare_additional_attacks.py` импортирует способности и добавляет ввод
в IMC_Rogue: **F — Blackhole**, **Q — Teleport**. ЛКМ остаётся основной атакой.
Клавиши и теги соответствуют Blueprint исходного курса. Персонаж выдаёт все три
атаки через ActionSystem; windup, cooldown и блокировка оглушением общие.
Как в исходных Blueprint, во время windup действует StatusEffect.Attacking:
атаки не совмещаются между собой и со спринтом. Blackhole расходует 25 Rage.
В ChestTest для одной пробной атаки нажмите H дважды, затем F; H наносит
тестовый урон, который даёт Rage. Teleport не требует Rage.

Teleport: 6000 см/с, детонация при попадании или через 0,2 с, остановка движения,
выключение коллизии и ещё 0,2 с до переноса Instigator. Native K2_TeleportTo
разрешает проникновение в геометрию; при неудаче игрок остаётся на месте.
Уничтожение снаряда отменяет таймер. Потерянный Instigator безопасно пропускается.

Сторонние эффекты и звуки хранятся только в локальном профиле DasRogueExternal.
После обновления ExternalAssets.json повторите установку ресурсов с
`--with-course-effects` и подготовку дополнительных атак. Без ресурсов остаются
простые видимые engine meshes. Для звука используются исходные SoundWave,
а не MetaSound-миксеры оригинала.

Проверка через общую очередь: `test-suite teleport-local rogue-additional-attacks repo=C:/src/DasForUE2-main`.


## Original player Animation Blueprint

The optional course animation profile retains GideonManny_AnimBlueprint's pose
graphs and Blueprint calculations: locomotion, jumps, aim offset, turn in place,
sprint/stun branches and the original montage slots. Gameplay remains daScript.
RogueAnimationComponent replaces the native parent's tag subscription and writes
only sprint/stun flags when relevant tags change. It does not tick or run DAS on
the animation worker thread.

Install acquired course assets with `Scripts/setup_external_assets.py
--source-content C:/src/ActionRoguelike/Content --with-course-effects
--with-course-animation` (add `--with-minions` to retain the AI profile).
In the original course editor, stop PIE, enable PropertyAccessNode and run:

```python
import runpy
runpy.run_path('C:/src/ActionRoguelikeDas/Scripts/export_course_animation.py',
              init_globals={'PORT_ROOT': 'C:/src/ActionRoguelikeDas'})
```

The export changes only a temporary duplicate, then removes it. It checks the
source Blueprint's SHA-256 before/after. The duplicate uses Engine.AnimInstance,
replaces two inherited flags with local variables, and adds the small
SetGameplayAnimationState adapter. A zero vector is materialized explicitly for
UE 5.8's const-reference validation; its value is unchanged. No original C++
module is needed to run the exported graph in the DAS project.

Then open ActionRoguelikeDas with PropertyAccessNode enabled and run
`Scripts/prepare_external_assets.py` from the editor's Python console. Its local
DA_Presentation selects ABP_CoursePlayer and SKM_Manny. The acquired assets,
exported Blueprint and generated presentation profile remain gitignored.
Without these external assets the public example retains its basic shape fallback.
The simpler generated ABP_Locomotion is still available when installing without
`--with-course-animation`.

The `rogue-course-animation` suite serializes source export and target PIE through
the shared build agent; it requires the local source comparison project.


## Burning — gameplay effect

`rogue_action_effect_burning.das` implements the original ActionEffect_Burning:
Duration=3 s, Period=1 s, DamageToApply=5, one instance per target/class. Reapplication
increments StackCount and normally refreshes duration, without restarting the
period timer. Each due tick applies `5 * StackCount` through native ApplyDamage.
The final due tick at duration expiry is preserved exactly once. Resetting duration
can be disabled through ResetDurationOnStackIncrease, as in the source effect.

Instigator and damage causer intentionally remain empty, matching the original
Blueprint's unwired pins. Damage therefore goes through normal native damage
events and the existing Health/Rage policy; it is not a direct Health assignment.
The source effect has no ActionName/GrantTags/BlockedTags and does not start VFX
or audio. Its optional icon belongs to the later HUD/presentation stage.

The playable `RogueMagicProjectileDemo` now defaults EffectOnHit to Burning, as
the original BP_MagicProjectile does. The generic RogueMagicProjectile remains
unconfigured. Designer overrides are preserved by normal reimport. Run
`Scripts/prepare_burning_effect.py` before importing projectile subclasses; the
standard preparation scripts already do this. `Scripts/prepare_burning.py`
prepares the isolated PIE test. Suite: `rogue-burning`.

For a manual check, open ChestTest, press Play and fire a single LMB shot at the
combat target with an action system. With 100 initial HP and no other hits,
the original 51 direct damage leaves 49 HP, then Burning changes it to
44, 39 and 34 at one-second intervals. Repeated hits increase the effect's stack
count, provided the target survives. No acquired assets are needed for this logic.


## Native Behavior Tree и daScript

Карта `/Game/DasRogue/Maps/BehaviorTest` использует `BP_RogueBehaviorController`.
Само дерево `/Game/DasRogue/AI/BT/MinionRangedBT`, Blackboard и три EQS-запроса —
Unreal assets. Их структура и настройки перенесены из исходного 992f860:
лечение → бой → патруль → ожидание. Старые ChestTest и PatrolTest сохраняют
свои изолированные сценарии и контроллеры.

Собственные узлы находятся в `rogue/rogue_bt_tasks.das`: HealSelf, LowHealth,
CheckRange, RangedAttack, FindPatrol и TargetActor EQS context. Это обычные
Blueprint-классы с native родителями BTTask/BTService/BTDecorator/EQSContext.
Unreal вызывает их Blueprint events, а сгенерированный DasForUE adapter
выполняет методы daScript. MoveTo, Wait, Cooldown, focus и выполнение EQS
оставлены штатному движку. RangedAttack использует общий DAS FireProjectile
сразу, без задержки player action. Дальность в дереве — 1000, условие LowHealth
строго меньше 0.3, HealSelf добавляет 100 HP. Ветка лечения ищет укрытие,
идёт туда, ждёт 1 секунду, лечится, ждёт ещё 1 секунду; cooldown — 20 секунд.

Blackboard хранит `TargetActor`, `WithinRange`, `MoveToLocation`,
`CurrentPatrolPoint`, `PreviousPatrolPoint`. `ue_behavior_tree.das` предоставляет
обращения к живому UBlackboardComponent; JSON-файла для передачи состояния нет.
PerceivedActors EQS выбирает ближайшую воспринимаемую цель. TargetActor context
читает Blackboard для запросов позиции атаки и укрытия. Стан ставит native brain
на паузу; смерть останавливает его до отключения tick контроллера.

`Scripts/prepare_behavior_tree.py` подготавливает assets и карту.
`Scripts/ai_assets/*.t3d` — редакторские описания структуры, а не runtime input.
Команда DasForUE `Das.AI.ImportText` создаёт только новые BT/Blackboard/EQS assets,
не перезаписывает и не сохраняет существующие. Двухэтапный импорт Unreal
создаёт объекты до заполнения ссылок, не вызывая промежуточный PostEditImport
у графовых узлов. Игра загружает готовые `.uasset`.
Исходное дерево можно повторно прочитать без изменения оригинальных assets
через `Scripts/export_original_ai.py` в редакторе оригинального проекта.

`roguedemo/rogue_behavior_minion.das` назначает новый контроллер для спавна.
`rogue/rogue_monster_spawner.das` выбирает класс из MonsterData, применяет Actions,
сохраняет список созданных монстров и очищает его при EndPlay. Повторное применение
того же профиля не дублирует действия. DropLoot использует уже выданное действие
и LootCoins из профиля. Бюджет и волны относятся к следующему этапу director.
HealthWidgetClass выбирает UMG-макет полоски здоровья; управление виджетом
реализовано в RogueHealthWidgetComponent на daScript.


### HUD и здоровье врагов

`RoguePlayerController.HUD` — компонент `rogue/rogue_hud_component.das`.
Он создаёт HUD только локальному игроку, подписывается на ActionSystem текущего
персонажа и показывает HP, Rage, монеты int64 и прицел. Список активных эффектов
показывает DisplayName (либо ActionName), StackCount и оставшуюся длительность.
`IconPath` — необязательный путь к Texture2D: загрузка асинхронная при создании
строки, каждый кадр ресурс не загружается. Пустой путь допустим.

В `Content/DasRogue/UI` лежат `WBP_RogueHUD`, `WBP_RogueHealth`, `WBP_RogueEffect`.
Это только UMG-макеты; игровая логика и подписки находятся в DAS.
`Scripts/prepare_hud_layouts.py` воспроизводит макеты редакторскими командами.
Во время игры Python и эти редакторские описания не используются.

`DA_RangedMinion.HealthWidgetClass` назначает `WBP_RogueHealth`.
`RogueHealthWidgetComponent` создаёт полоску после первого несмертельного урона,
обновляет HP по событиям и проецирует позицию через native UMG с учётом DPI.
За камерой виджет скрывается, при смерти и EndPlay удаляется. Tick позиции
включён только пока существует полоска; при смене персонажа HUD снимает старые
подписки. Поля класса виджета в компонентах позволяют заменить макеты.

Проверка: suite `rogue-hud` в DasForUE, сценарий
`Scripts/run_hud_test.py`, результат `Saved/Tests/rogue_hud_pie.json`.


### Директор и волны монстров

Карта `/Game/DasRogue/Maps/DirectorTest` содержит `RogueSpawnDirector` на daScript.
В Play он накапливает бюджет по `C_DirectorIncome`, выбирает строку
`DT_DirectorMonsters` по SpawnWeight и запускает native EQS. После асинхронной
загрузки MonsterData общий спавнер создаёт нужный класс и выдаёт действия.
`DA_DirectorMinion` использует уже перенесённого монстра с native Behavior Tree.
Скрипты генерации и CSV нужны редактору; во время игры загружаются `.uasset`.

В акторе настраиваются `Configurations`, `GlobalStartingSeed`, `BotLimit` и
`AutoStart`. В каждом `DA_Director` — таблица, EQS, кривая дохода, начальный бюджет,
TickInterval и TimeBetweenWaves. Кривая заменяет исходный inline RuntimeFloatCurve
внешним редактируемым CurveFloat; без неё используется CreditsPerSecond.
Значение кривой вычисляется по времени мира. Дробные бюджет/стоимости остаются float,
как в оригинале; денежный кошелёк игрока по-прежнему int64.

Один актор координирует несколько runtime-слотов, соответствующих исходному массиву
Directors. У каждого свой FRandomStream seed, полученный из общего seed. Строки
таблицы сортируются по имени; нулевые/отрицательные веса и некорректные стоимости
не участвуют в выборе. Проверка стоимости выполняется после взвешенного выбора,
как в исходнике. При недостатке средств директор ждёт TimeBetweenWaves.

Место в общем лимите резервируется до запуска EQS и сохраняется при загрузке
профиля. Перед созданием снова проверяется число живых монстров во всём мире;
мёртвый монстр освобождает лимит до удаления ragdoll. Неудачный EQS, загрузка или
создание возвращают бюджет. Это намеренное отличие от исходника, списывавшего
стоимость до запроса без возврата. `SetEnabled(false)` отменяет запросы и загрузку,
возвращает резервы и приостанавливает доход. `Shutdown` дополнительно удаляет
созданных монстров и их контроллеры. EndPlay освобождает те же ресурсы без
повторного управления native tick уничтожаемого актора.

Основные файлы: `rogue/rogue_spawn_director.das`, `rogue_director_slot.das`,
`rogue_director_config.das` и `rogue_director_types.das`.
`Scripts/prepare_director.py` воспроизводит данные и расстановку на открытой
DirectorTest; макеты EQS находятся в `Scripts/ai_assets/EQS_Director*.t3d`.
Suite для PIE: `rogue-director` в общей очереди DasForUE.

Проверено: 14 сценариев PIE, включая GC, общий лимит, seed, отмену EQS,
возврат бюджета и удаление директора; журнал и завершение игры прошли проверку.

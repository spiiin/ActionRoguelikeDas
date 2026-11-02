# ActionRoguelike на daScript

Исходная версия: Tom Looman, ActionRoguelike, ветка UE5.6-CourseProject, коммит 992f860922373d50db05eacc5e1fce952ed88c13.

- Оригинал: https://github.com/tomlooman/ActionRoguelike
- Курс: https://tomlooman.com/courses/unrealengine-cpp/
- Локальная интеграция: C:/src/DasForUE2-main, Unreal Engine 5.8.3.

Вся игровая логика находится в daScript. C++ тест в репозитории DasForUE импортирует и проверяет классы; он не является реализацией игровой логики. Разрешение автора на публикацию и лицензия производного порта уточняются; MIT-лицензия DasForUE не переносится автоматически на этот пример. Ассеты курса сюда не скопированы.

## Первые классы

Content/Das/Scripts/rogue_interaction_interface.das объявляет настоящий UE Blueprint Interface с методом Interact без параметров.

Content/Das/Scripts/rogue_interaction.das вызывает этот интерфейс из daScript, отвергая пустые ссылки и объекты без нужного интерфейса.

Content/Das/Scripts/rogue_item_chest.das реализует RogueItemChest: два StaticMesh-компонента, редактируемые скорость и целевой pitch, включение tick при взаимодействии, равномерное вращение крышки и overridable событие ChestAnimationComplete. Начальный tick отключается в BeginPlay. Профили collision устанавливаются там же, после создания SCS компонентов; в C++ оригинале они задаются в конструкторе.

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

Тестовый runner копирует три исходника и Tests/Das/rogue_item_chest_observer.das в Content/Das/Scripts smoke-проекта. Канонические исходники находятся здесь. Автотест DasForUE.Ports.RogueChest проверяет интерфейс, компоненты, tick, углы, повторное взаимодействие и две независимые копии. Результаты и ограничения запуска фиксируются в VALIDATION.md после проверки.

## Выбор цели и клавиша E

Первый этап реализован полностью: `rogue_interaction_component.das` принадлежит контроллеру и каждый tick выбирает объект в радиусе 800 по весу расстояния и направления камеры. `rogue_player_controller.das` создаёт этот компонент, устанавливает TeamId=1 и подключает Enhanced Input после готовности локального ввода. Вся игровая логика находится в daScript.

В `Content/Das/Scripts/rogue_player_controller.das` заданы ссылки по умолчанию на `/Game/DasRogue/Input/IA_Interact` и `IMC_Rogue`. Эти ресурсы создаёт `Scripts/prepare_interaction.py` до импорта класса. Mapping связывает E с Boolean action; событие Started вызывает взаимодействие один раз за нажатие. Удержание E не вызывает повторных команд. Это осознанное отличие от Triggered в исходном контроллере.

Компонент отбрасывает объекты без интерфейса, безопасно обрабатывает отсутствие pawn и обновляет выбор непосредственно перед вызовом Interact. Автоматический таймер открытия удалён. На карте используется `RogueInteractiveChest`, наследующий только поведение сундука.

Для проверки открыть `ActionRoguelikeDas.uproject`, карту `/Game/DasRogue/Maps/ChestTest`, нажать Play, щёлкнуть в игровой viewport и нажать E. Сундук открывается за 2,4 секунды. Камера PlayerStart уже находится в радиусе взаимодействия и смотрит на сундук. Персонаж BP_RogueCharacter реализован на daScript: WASD, мышь и Space; камера от третьего лица через SpringArm.

Подготовка карты выполняется редакторским Python-скриптом `Scripts/prepare_interaction.py`: создаёт input assets, импортирует классы, назначает daScript-контроллер через GameMode и заменяет прежний автоматический demo actor. Скрипт использует простые engine cube meshes; ассеты курса не требуются.

Suite `rogue-interaction` проверяет настоящий PIE и ввод E через PlayerController.InputKey, выбор двух сундуков, удержание клавиши, выход из радиуса, удаление цели, отсутствие pawn и очистку runtime после EndPIE. Команда агенту: `test-suite rogue-input-local rogue-interaction repo=C:/src/DasForUE2-main`.


## RogueProjectile и ЛКМ

`rogue_projectile.das` переносит базовый ARogueProjectile из зафиксированной версии курса: SphereComponent радиусом 16, ProjectileMovement со скоростью 2000 и нулевой гравитацией, LoopedNiagaraComponent и LoopedAudioComponent, срок жизни 30 секунд, исключение Instigator из swept collision, OnComponentHit → разовые эффекты → Destroy. Урона в этом базовом классе нет, как и в оригинале. HasImpacted защищает от повторной обработки попадания.

`rogue_projectile_demo.das` добавляет видимую сферу из Engine/BasicShapes и отключает её собственную коллизию. Авторские ассеты курса не используются. Базовые ExplosionSound/ExplosionEffect опциональны. Демонстрационный потомок назначает engine sound 1kSineTonePing и Niagara template RadialBurst; их можно заменить своими ресурсами. Зацикленные эффекты по умолчанию пусты.

Текущий `RoguePlayerController` привязывает Boolean `IA_Fire` к Started для ЛКМ. Он запрашивает Action.PrimaryAttack у компонента персонажа. RogueActionProjectileAttack выдерживает задержку каста и создаёт экземпляр ProjectileClass с Owner=controller и Instigator=pawn. Поведение стрельбы написано на daScript. E продолжает открывать сундук.

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

Content/Das/Scripts/rogue_character.das переносит движение, взгляд и прыжок
RoguePlayerCharacter. GameMode использует BP_RogueCharacter вместо DefaultPawn.
W/S — вперёд/назад относительно yaw камеры, A/D — влево/вправо, мышь — обзор,
Space — прыжок; отпускание Space вызывает StopJumping. E и ЛКМ остаются
в daScript контроллере. Камера прикреплена к SpringEndpoint у SpringArm длиной
350 см; персонаж поворачивается по направлению движения. Cone — временная
геометрия из стандартных ресурсов движка, без collision; движение использует
нативную капсулу Character. Mesh/анимации курса не импортировались.

WalkSpeed=450, JumpVelocity=500, AirControl=0.2 редактируются в Class Defaults
BP_RogueCharacter и применяются скриптом в BeginPlay. Состояние ControlsBound
и счётчики событий доступны для диагностики. Подключены Attributes и первый
срез смерти игрока; система способностей относится к следующим этапам. Снаряд
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
Play. Анимация смерти, ragdoll, respawn и возрождение пока не реализованы.
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
движении: MaxWalkSpeed меняется с 450 на 720 (SpeedMultiplier=1.6). Отпускание
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
нет скелетного меша/AnimBP, поэтому видимого montage пока нет. Ресурсы курса не копировались.

Автопроверка: suite `rogue-projectile-attack`, результат
`Saved/Tests/rogue_projectile_attack_pie.json`. Подготовка мигрирует старый контроллер
через `fields=archive_remove_with_dependencies`; удалённые поля архивируются.
Повторная подготовка использует обычный Reimport.

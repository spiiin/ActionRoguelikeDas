# ActionRoguelike на daScript

Порт всей игровой логики ActionRoguelike на daScript для DasForUE. Если для очередного класса не хватает возможностей интеграции, расширяем DasForUE и затем переносим класс полностью. Постоянных C++ реализаций игровых систем в порте не оставляем.

## Исходная версия

- Репозиторий: https://github.com/tomlooman/ActionRoguelike
- Ветка: UE5.6-CourseProject.
- Зафиксированный коммит: 992f860922373d50db05eacc5e1fce952ed88c13.
- Порядок ниже относится к этой версии, а не к текущему master.
- Разрешение на публичное распространение производного порта и его лицензия уточняются у Tom Looman. Не присваивать порту MIT автоматически. Для сторонних ассетов вести отдельный учёт происхождения и условий.

## Граница между игровым кодом и интеграцией

В daScript переносим поведение Actor, Component, UObject, интерфейсов, способностей, атрибутов, AI, UI, игровых режимов и подсистем. Blueprint может содержать оформление, ссылки на ресурсы и настройки, но перенесённая игровая логика должна выполняться в daScript.

C++ используется внутри DasForUE для универсальной связи с Unreal Engine: регистрации классов и свойств, создания объектов, вызова методов, передачи virtual callbacks, событий, delegates и работы GC. Такие механизмы не должны содержать игровую логику сундука, снаряда или Action System. Конкретный механизм генерации или регистрации классов определяется после изучения текущего устройства DasForUE.

Полный перенос означает сохранение поведения исходной версии. Изменения поведения и исправления ошибок отмечаем отдельно. Не добавляем сетевую поддержку, сохранения или другие возможности только потому, что они есть в другой ветке: сначала проверяем их наличие в зафиксированном исходнике.

## Подготовка DasForUE

До реализации определить расположение репозитория DasForUE и используемую версию UE. Сопоставить требования ниже с существующим API обёртки; этот план не утверждает, что перечисленные возможности сейчас отсутствуют.

Подготовить регистрацию скриптовых классов и редакторских свойств, корректное конструирование CDO и default subobjects, наследование и вызов базового метода. Определить порядок жизненного цикла Actor и Component, а также доступ к World для UObject с Outer.

Определить модель владения ссылками между UE GC и daScript. Отдельно обработать Destroy, EndPlay, удаление UObject, подписки и таймеры. Временные ссылки вроде const FHitResult& нельзя сохранять после callback без копирования.

## Порядок переноса

### Этап 1 Взаимодействие

Статус на 2 ноября 2026: реализован в daScript. Интерфейс, сундук, выбор цели и контроллер с Enhanced Input E проходят целевые автотесты. Проверки и ограничения — в VALIDATION.md.

Классы: URogueInteractionInterface и IRogueInteractionInterface, ARogueItemChest, URogueInteractionComponent, ARoguePlayerController.

Порядок: интерфейс, сундук, компонент выбора объекта, контроллер и ввод взаимодействия. Компонент в оригинале принадлежит PlayerController и выбирает цель через sphere overlap с весом расстояния и направления камеры.

Биндинг: реализация UE интерфейсов в daScript, BlueprintNativeEvent и BlueprintImplementableEvent в обе стороны, Tick и TickComponent, editable properties, mesh components и attachment, FVector и FRotator, FMath, collision profiles, OverlapMultiByChannel, FOverlapResult, массивы и выходные параметры, PlayerCameraManager, Enhanced Input. Для контроллера также потребуется IGenericTeamAgentInterface и FGenericTeamId.

Готовность: daScript контроллер выбирает сундук и открывает его; завершение анимации вызывает событие. Изменённые в редакторе параметры сохраняются и действуют в игре.

### Этап 2 Снаряды и физика

Статус на 4 ноября 2026: базовый/магический снаряды, ExplosiveBarrel и Blackhole
реализованы и проверены в PIE. Teleport и действия Blackhole/Teleport также
прошли 10 групп PIE-проверок: rogue-teleport-20261104y. Управление
соответствует исходному IMC_DefaultPlayer: F — SecondaryAttack/Blackhole,
Q — SpecialAttack/Teleport. Итог приёмки фиксируется в VALIDATION.md.

Классы: ARogueProjectile, ARogueExplosiveBarrel, ARogueProjectileBlackhole, ARogueProjectileTeleport.

Порядок: базовый снаряд, бочка, blackhole, teleport. Базовый снаряд не наносит урон; бочка использует физический импульс, а не radial damage. До этапа 5 урон бочке можно подать из тестового daScript сценария.

Биндинг: PostInitializeComponents и BeginPlay, USphereComponent, UProjectileMovementComponent, OnComponentHit и OnComponentBeginOverlap, FHitResult, lifespan, Destroy, Instigator, TakeDamage и FDamageEvent, FTimerHandle с запуском/отменой/проверкой, URadialForceComponent, физические импульсы, Niagara, audio, SpawnActor с классом и параметрами, TeleportTo с обработкой результата.

Готовность: попадания обрабатываются один раз, бочка взрывается после задержки, blackhole удаляет физические объекты, teleport корректно разрешает конкуренцию попадания и таймера. Уничтожение владельца не оставляет небезопасных callback.

### Этап 3 Атрибуты

Типы: FRogueAttribute, EAttributeModifyType, URogueAttributeSet, URogueHealthAttributeSet, URoguePawnAttributeSet, URoguePlayerAttributeSet, URogueMonsterAttributeSet.

Биндинг: отражаемые структуры и их mutable поля, наследование UObject, Outer, редакторские вложенные объекты, создание default subobjects, связь с CharacterMovement.MaxWalkSpeed.

Нужен способ обнаруживать атрибуты, эквивалентный текущему TFieldIterator<FStructProperty>. Выбрать отражаемые скриптовые свойства либо явную регистрацию атрибутов в daScript. При явной регистрации сохранить семантику имён Gameplay Tags и изменения Base/Modifier; не хранить указатели, которые могут стать невалидными при перезагрузке скрипта.

Готовность: Health ограничен HealthMax, модификаторы учитываются, MoveSpeed обновляет компонент движения.

### Этап 4 Система способностей

Классы: URogueAction, URogueActionEffect, URogueActionSystemComponent. Сюда же SharedGameplayTags и необходимая часть RogueGameTypes.

Эти классы имеют взаимные зависимости: реализовать совместно, проверять по частям — создание и владение, изменение атрибутов, запуск/остановка, эффекты и стеки.

Биндинг: Gameplay Tags и containers, массивы и словари, TSubclassOf и проверка наследования, NewObject с Outer, полиморфные callbacks, native и dynamic delegates, subscription handles, soft object references, время мира, периодические таймеры и удаление эффектов.

Готовность: стоимость, cooldown и блокирующие теги работают как в исходнике; эффект тикает, обновляет длительность при увеличении стека и удаляется без оставшихся таймеров/подписок. World для скриптовых UObject разрешается явно и проверяется в PIE и packaged build.

### Этап 5 Персонаж и бой

Классы: ARoguePlayerCharacter, URogueAction_ProjectileAttack, ARogueProjectileMagic, URogueActionEffect_StunMonster, URogueActionEffect_Overwhelm, URogueGameplayStatics, URogueAnimInstance.

Биндинг: Character, SpringArm, Camera, Enhanced Input values и callbacks, движение и прыжок, montage, sockets, line trace, параметры SpawnActor, point damage, AI hearing, overlay material и custom primitive data, animation lifecycle и доступ к pawn.

Готовность: движение и атака выполняются из daScript; магический снаряд наносит урон, толкает физические объекты и применяет эффект. Реакция на здоровье, смерть, cooldown и stun соответствуют исходной версии.

### Этап 6 Подбор предметов и монеты

Статус на 3 ноября 2026: pickup, лечение, подсистема монет, генератор и DropLoot реализованы и проверены в PIE. Остаётся конфигурация ресурсов через DeveloperSettings и асинхронная загрузка, как в оригинале.

Классы: ARoguePickupActor, ARogueHealthPickup, URogueCoinPickupSubsystem, ARogueCoinTestActor, URogueAction_DropLoot.

Порядок: обычный pickup, лечение, подсистема монет, тестовый генератор монет, выдача добычи.

Биндинг: world subsystem lifecycle, доступ к подсистеме, bulk arrays, instanced mesh API и другие API, фактически используемые подсистемой, random streams, navigation queries, overlaps и UObject references. Перед реализацией разобрать внутреннее представление монет; не заменять его Actor на каждую монету без отдельного решения.

Готовность: лечение учитывает максимум, подбор монет обновляет ресурс, смерть выдаёт добычу. Массовые операции сохраняют смысл исходного алгоритма.

### Этап 7 AI

Классы: ARoguePatrolPoint, URogueMonsterData, ARogueAIController, ARogueAICharacter, URogueBTService_CheckRangeTo, URogueBTDecorator_IsLowHealth, URogueBTTask_FindNextPatrolPoint, URogueBTTask_HealSelf, URogueBTTask_RangedAttack, URogueEnvQueryContext_AlivePlayers, URogueEnvQueryContext_TargetActor.

Биндинг: AIController, perception, teams, Behavior Tree tasks/services/decorators, blackboard, EQS context callbacks, navigation, data assets и ссылки на классы. Для BT определить семантику instancing и NodeMemory: изменяемое состояние не должно случайно разделяться между ботами.

Готовность: два независимых бота патрулируют, выбирают цель, атакуют и лечатся; состояния деревьев не смешиваются.

### Этап 8 UI

Классы: URogueWorldUserWidget, URogueMainHUDWidget, ARogueHUD.

Биндинг: UserWidget lifecycle, BindWidget, создание и размещение widgets, CanvasPanel, проекция координат в экран, владение widgets и подписки на игровые события. Игровые обработчики из Blueprint также перенести в daScript после инвентаризации assets; визуальную разметку можно оставить в UMG.

Готовность: HUD отражает атрибуты и способности, мировые widgets следуют за объектами, повторное открытие UI не дублирует подписки.

### Этап 9 Игровой режим и запуск

Классы: ARogueGameMode, ARoguePrimaryGameMode, URogueGameInstance, URogueDeveloperSettings; оставшиеся структуры RogueGameTypes.

Биндинг: GameMode/GameInstance lifecycle, конфигурация и developer settings, DataTable, curves, random streams, EQS и загрузка ресурсов по фактическим зависимостям классов.

Готовность: игра запускается с собственными скриптовыми классами, создаёт игрока и противников и проходит полный игровой цикл. Проверить переходы между картами и очистку состояния мира.

## Как расширять обёртку

1. Для каждого класса выписать реально вызываемые API и входящие callbacks.
2. Найти соответствия в DasForUE и отметить конкретный пробел.
3. Воспроизвести пробел небольшим daScript примером.
4. Добавить универсальную поддержку в DasForUE и проверить воспроизводящий пример.
5. Перенести поведение класса на daScript и сравнить с исходником.
6. Отметить редакторские свойства, assets и зависимости, необходимые для запуска.

Не создавать постоянные C++ обходные реализации игровой логики. Временный тестовый стенд на daScript допустим для проверки класса раньше его игровых зависимостей.

## Проверка завершённого порта

- Игровые классы и обработчики реализованы на daScript; C++ содержит только инфраструктуру DasForUE.
- Все входящие virtual/event/delegate callbacks доходят до скрипта и корректно вызывают базовую реализацию там, где она нужна.
- Проверены PIE, повторный запуск PIE, GC, уничтожение объектов и packaged build.
- Если DasForUE поддерживает перезагрузку скриптов, проверены ссылки, таймеры и подписки после неё.
- Проведено сравнение поведения игровых систем с зафиксированным исходником.
- Проверена игровая логика внутри Blueprint assets; оставшаяся визуальная настройка отделена от скриптового поведения.
- Разрешение на публикацию и лицензии кода и ресурсов оформлены до публичного распространения.

## История переноса

На 2 ноября 2026 перенесены RogueInteractionInterface, RogueItemChest,
RogueInteractionComponent, RoguePlayerController и RogueProjectile. На карте
ChestTest работают E, крышка с задним шарниром и ЛКМ.

Добавлен первый срез здоровья/урона: RogueAttributeComponent,
RogueMagicProjectile и тестовая RogueTargetDummy с HP, цветом и смертью.
Все игровые обработчики — daScript; C++ добавляет только универсальные API.
Регрессии и ручные интеграционные проверки перечислены в VALIDATION.md.

Перенесён первый срез RogueCharacter: движение, камера SpringArm и прыжок вместо DefaultPawn.
Перенесены точка запуска снаряда от персонажа с прицеливанием по камере, здоровье игрока и первый срез смерти.
Добавлены система действий со Sprint и RogueActionProjectileAttack с задержкой каста и cooldown. Анимации, respawn и полноценная система эффектов ещё впереди.
Затем — направленный урон, физический импульс, AI и action effects.
Разрешение на публикацию и лицензия остаются отдельным незавершённым вопросом.

## Action System / Sprint — завершён первый срез

Добавлены RogueAction, RogueActionSystemComponent и RogueActionSprint. Работают
выдача/удаление действий, активные/блокирующие теги, стоимость ресурса, cooldown,
ускорение по Shift, отмена по оглушению и смерти. Фабрика ScriptObject поддерживает
наследников через базовый authored reference; сильное владение и освобождение
действий проверены принудительным GC. Игровой код остаётся в daScript.

RogueActionProjectileAttack перенесён: контроллер запрашивает действие, способность
управляет выстрелом, задержкой и cooldown. Далее — эффекты/модификаторы, остальные способности,
анимации, AI и дальнейшие срезы исходного проекта.


## Action effects — завершён первый срез

Добавлены RogueActionEffect и RogueActionEffectStun: автоматический запуск,
период, длительность, стеки с настройкой обновления срока и очистка при
удалении/Shutdown/EndPlay. Проверочный периодический эффект масштабирует
изменение Rage по числу стаков. Overwhelm и применение эффектов от попаданий
перенесены следующим срезом, описанным ниже.

Локальный профиль Manny/Gideon уже покрывает наземное движение, атаку и смерть;
полная анимационная машина состояний и respawn остаются впереди.

## Overwhelm и эффекты попадания — завершён срез

Перенесён RogueActionEffectOverwhelm: окно соседних событий урона, игнорирование
лечения и урона во время stun, выдача эффекта по порогу, очистка подписки при
остановке/удалении/смерти. RogueMagicProjectile получил EffectOnHit; проверка
наследования отклоняет неподходящий класс до создания экземпляра. На ChestTest
добавлена отдельная RogueCombatTarget с ActionSystem и отображением stun.

Следующий боевой срез: point damage/HitResult, физический импульс и AI hearing.
Далее — подбор предметов/добыча, AI, UI и полный игровой цикл согласно этапам выше.

## AI — первый боевой срез проверен

Добавлены AI Character, generic-parent AIController и ranged action на daScript.
Сценарий: зрение/слух → живая player-pawn цель → direct MoveTo → ranged action;
stun останавливает бой, потеря LOS отменяет атаку, память цели ограничена,
смерть выключает действия и уничтожает контроллер. Новый тест `rogue-ai` готов.

После обновления зависимости `rogue-ai` и `rogue-projectile-attack` прошли
реальный PIE; результаты зафиксированы в VALIDATION.md. Далее — NavMesh/
обход препятствий, патруль и поиск цели, лечение, награда/добыча.


## AI Minion — локальное представление

Подключён ranged Dawn Minion: locomotion, подготовка выстрела, попадание,
stun и удержание позы смерти. Профиль выбирает монтаж, задержку и сокет оружия;
решения и реакции выполняются в daScript. Попадание отменяет ожидающий выстрел.
Ресурсы устанавливаются отдельно через `--with-minions`, их производные остаются
в игнорируемом `DasRogueExternal`. Отсутствующий профиль оставляет конус.
Целевая проверка `rogue-ai-presentation` покрывает девять групп в реальном PIE.


## NavMesh и патруль — проверено в PIE

Добавлены `RoguePatrolPoint` и отдельный `RoguePatrolController`, наследующий
боевой AI. Граф использует native GetPathLength, двусторонние связи и ближайшую
начальную точку; предыдущая точка исключается из случайного выбора, когда есть
другой выход. Движение использует управляемый MoveTo с полным NavMesh-путём.
Срез не переносит Behavior Tree или его ресурсы.

В отличие от редакторского OnConstruction исходного PatrolPoint, граф строится
явно после готовности runtime NavMesh. Повторная сборка доступна через
RefreshPatrolGraph. Недоступные nav-данные откладывают перестройку, сохраняя
старые связи. Отдельная карта PatrolTest готовится Scripts/prepare_patrol.py;
ChestTest сохраняет прежний боевой сценарий. `rogue-patrol-v8-20261103` прошёл
все девять групп реального PIE: движение, прерывания, удаление цели и очистка.
Подробности и отдельное ограничение дискового AST-кэша — в VALIDATION.md.


## Pickup и лечение — проверено в PIE

RoguePickupActor и RogueHealthPickup реализованы на daScript. По умолчанию
сохранён overlap-подбор с одноразовым удалением из исходной версии 992f860.
RogueHealthPickupDemo включает E и пятисекундное повторное появление на ChestTest.
Лечение проходит через RogueAttributeComponent в общий AttributeSet; прежнее
событие OnHealthChanged сохраняет поведение предметов и их обработчиков.

Available резервируется до применения здоровья и доставки событий; повторный
вход не вызывает второе лечение. Использованный предмет скрыт и не участвует
в коллизии. Таймер принадлежит актору и отменяется при его уничтожении.
Dead Pawn и некорректное неположительное лечение отклоняются явно.
`rogue-pickup-v2-20261103`: восемь групп реального PIE PASS.
Подсистема монет и награды/DropLoot также перенесены и проверены ниже.


## Coins / DropLoot — verified in PIE

RogueCoinPickupSubsystem batches coins in one world-owned ISM instead of creating
an Actor per coin. RogueActionDropLoot runs before the dying AI shuts down its
actions, uses RogueMonsterData.LootCoins (default ten without data), and preserves
the sum when navigation placement fails. RogueCoinTestActor generates batches.
Currency totals and player wallet use reflected int64; HUD refreshes on the
typed balance-change event. MonsterData's remaining director/UI fields are
declarations only; those systems remain future stages.


## Сверка стрельбы с оригиналом 992f860 — первый срез проверен

Удержание ЛКМ повторяет атаку через Triggered, с прежней задержкой каста и cooldown.
Прицеливание использует 5000 см и канал Projectile. Защита от создания снаряда
за препятствием сохранена; её sweep использует тот же канал. Смена default дальности
проходит через Reimport с preserve_overrides. Проверено 17 групп в реальном PIE
на изолированной копии без незавершённых монетных изменений; подробности в VALIDATION.md.
AttributeSet и получение Rage от урона реализованы и проверены ниже.

Acceptance: `15` real PIE groups PASS, including an exact balance above 2^53, overflow rejection, native damage, GC and EndPIE cleanup. See VALIDATION.md.


## AttributeSet и Rage — проверено в PIE

На daScript перенесены RogueAttributeSet, Health/Pawn/Player/Monster-наследники и
RogueAttributeModifyType (Base, Modifier, OverrideBase). Значение равно Base + Modifier;
скорость равна MoveSpeed × MoveSpeedMultiplier. Health.Base ограничивается HealthMax,
как в оригинале 992f860. Понижение максимума дополнительно уведомляет наблюдателей
здоровья; отдельное событие максимума обновляет UI даже без изменения текущего HP.

Общий ScriptObject удерживается отражёнными ссылками компонентов здоровья и действий.
BaseValues/Modifiers — сериализуемые карты; RogueAttribute — обычный снимок значения для
Option-запросов. Прежние Health/HealthMax, Resources и параметры скорости служат видами
для просмотра. Runtime-изменения выполняются через ModifyAttribute/ApplyHealthChange.
Смена Player/Monster-набора сохраняет общие атрибуты и удаляет несовместимые, включая Rage.

Нативное событие урона передаётся в daScript: игрок получает Rage = входящий урон × 0.75,
включая overkill до ограничения HP. Лечение не даёт Rage; у Monster-набора его нет.
Coins остаются отдельным int64. Существующая настройка персонажа WalkSpeed=450 сохранена;
сам PawnAttributeSet имеет исходный default 550, Monster — 450. Stun AI отключает режим
движения, поэтому пересчёт атрибутов не разрешает движение до окончания эффекта.

rogue-attributes-v16-20261103: 12 групп реального PIE PASS, включая значения и события,
Rage/UI, спринт, повторный вход, смену набора, удержание нового и сборку старого объекта.
GenericParents PASS: аддитивные callback/метаданные при независимых потребителях,
отказ при удалении callback, контракт наследника без собственных методов после GC
и повторного импорта. Исправления находятся в DasForUE2-main; packaged-сборка этого
этапа отдельно не проверялась. Регрессии соседних систем записываются в VALIDATION.md.


## ExplosiveBarrel — проверено в PIE

RogueExplosiveBarrel перенесён на daScript: PhysicsActor mesh, отключённое влияние
на навигацию, прикреплённый RadialForceComponent, фитиль 3 секунды, однократный
импульс 150000 в радиусе 750 и собственные линейный/угловой импульсы по 1000
с изменением скорости. Radial damage не добавлен. Визуальные эффекты необязательны.

Горение использует заранее созданные дочерние Niagara/audio-компоненты вместо
динамического SpawnAttached. Взрыв явно останавливает их; при EndPlay завершение
компонентов выполняет Unreal, а таймер отменяется управляемым teardown владельца.
Явная защита от повторного Explode и отказ при некорректной задержке — улучшения
по сравнению с исходником 992f860. Native OnTakeAnyDamage адаптирует игровой
путь ApplyDamage; C++ игровой логики бочки нет.

`rogue-barrels-v6-20261103`: восемь групп PIE PASS, журнал runtime/ensure/teardown
чистый. Отдельная карта BarrelTest исключает зависимость от текущего состояния AI.
Следующие классы этапа 2: RogueProjectileBlackhole и RogueProjectileTeleport.


## Повторная сверка с оригиналом — 3 ноября 2026

Сравнение исходников 992f860 с портом ac7c332 и текущим рабочим деревом.
Учтены новые, ещё не закоммиченные бочка и blackhole. Это статическая повторная
сверка кода и существующих receipts; новых запусков PIE для аудита не было.
Численные defaults ниже относятся к объявлениям кода: итоговые значения оригинальных
Blueprint/CDO необходимо отдельно подтвердить перед изменением баланса.

Закрыты прежние пробелы: Triggered/удержание основной атаки, дистанция 5000 и канал
Projectile, point damage/noise/impulse/effect-on-hit, Base/Modifier/OverrideBase,
наборы атрибутов и Rage, эффекты/Overwhelm/stun, NavMesh-патруль, лечение,
пакетные монеты и DropLoot. Для AttributeSet и соседних систем есть 65 групп PIE PASS.
Бочка отдельно прошла восемь групп (rogue-barrels-v6-20261103).

### Что исправить в уже перенесённом поведении — шесть пунктов закрыты 4 ноября 2026

Сверка фактических CDO оригинала 992f860 и native BehaviorTree-задачи подтверждает
урон BP_MagicProjectile=51, MoveSpeed игрока=550, MoveSpeed AI=450 и MaxBulletSpread=5.
CDO CharacterMovement показывает 600, но BeginPlay использует скорость AttributeSet.

1. Персонаж добавляет созданный снаряд в native MoveIgnoreActorAdd; обратное
   игнорирование instigator сферой сохранено. PIE сравнивает sweep через свой и чужой снаряд.
2. AI публикует AISense_Damage с реальным controller/pawn instigator и фильтром
   Friendly. Тип Damage проектируется в AIStimulus; цель приобретается вне Sight/Hearing.
3. Смерть AI останавливает thinker/движение и действия, отключает capsule,
   ставит Ragdoll, включает физику тел, приостанавливает анимацию и оставляет труп на 10 секунд.
   В порте thinker расположен в контроллере; его Tick останавливается вместо BT StopLogic.
4. Общий RogueHitFlashComponent у игрока/AI пишет время удара в CustomPrimitiveData[0],
   включает overlay и выключает его через секунду. Повторный удар перезапускает таймер.
   Материал M_HitFlash генерируется нашим скриптом, исходный лицензируемый материал не копируется.
   Попадание больше не запускает дополнительный hit montage и не отменяет pending shot.
5. AI применяет разброс от фактического muzzle: pitch [0,5], yaw [-5,5]; настройка доступна
   как MaxBulletSpread. Player aim остаётся без случайного разброса.
6. Баланс установлен по фактическим исходным defaults: 51 / 550 / 450.

Проверка: `rogue-combat-parity`; доказательства и ограничения — VALIDATION.md.
Дисковый editor module cache временно отключён только в этом проекте из-за
воспроизводимого warm-start падения; передача диагностики — MODULE_CACHE_REPRO.md.

### Что ещё нужно перенести

1. **Blackhole — закончить текущий срез.** Реализация уже существует в
   rogue_projectile_blackhole.das. Последний доступный на момент сверки receipt
   rogue_blackhole_pie.json завершился отказом импорта класса; успешной приёмки
   пока нет. Не считать его ни отсутствующим исходником, ни готовой системой.
2. **Teleport projectile.** Две задержки по 0.2 секунды по умолчанию, переход по hit
   или таймеру, остановка движения/loop-эффектов, TeleportTo instigator и очистка таймеров.
3. **Остальные игровые способности и input.** Настройки Action_Blackhole и
   Action_Teleport, SecondaryAttack/SpecialAttack, их цены Rage, cooldown и presentation.
   Текущая фабрика и ProjectileAttack могут использоваться повторно.
4. **Игровой Burning effect.** Базовый периодический эффект есть и проверен, но
   конфигурация/поведение исходного ActionEffect_Burning ещё не представлены игровым
   классом. Тестовый периодический эффект сам по себе этот Blueprint не переносит.
5. **Полный AI-сценарий.** Behavior Tree/blackboard, LowHealth и HealSelf, ranged task,
   EQS AlivePlayers/TargetActor. Патруль, perception и прямое преследование уже есть;
   их нужно связать с этим сценарием. В MinionRangedBT найдены зависимости четырёх
   исходных native task/service/decorator классов.
6. **MonsterData целиком.** Сейчас используется LootCoins; MonsterClass,
   Actions и HealthWidgetClass объявлены, но полный runtime-путь их применения
   через director/spawn и UI ещё отсутствует.
7. **HUD и мировые widgets.** RogueHUD, MainHUD/WorldUserWidget, экранная проекция
   с DPI, health/rage, crosshair и effect bar/slots, игровые обработчики из UMG Blueprint.
   Текущие TextRender-метки — демонстрационное представление.
8. **RogueAnimInstance и состояние анимаций.** Locomotion и montage уже подключены;
   переходы состояния по GameplayTag Sprinting/Stunned ещё не перенесены как
   эквивалент исходного AnimInstance.
9. **Игровой цикл.** PrimaryGameMode/directors с кредитами по кривой, weighted
   DataTable, seed, bot limit, EQS spawn, async MonsterData, deferred spawn и выдача
   Actions; GameInstance.AliveMonsters и очистка при смене мира. DeveloperSettings
   с soft mesh/sound и их async загрузкой для монет.
10. **Blueprint-only окружение и итоговая карта.** Отдельно разобрать BP_Lever и
    BP_ProjectileSpammer. Собрать единый игровой сценарий с NavMesh, противниками,
    спавном, UI и способностями; ChestTest/PatrolTest/BarrelTest пока проверяют срезы.

Осознанные отличия, которые не следует автоматически считать дефектами: защита
выстрела от ближнего укрытия, отмена pending cast при stun/удалении, int64-кошелёк,
фильтр интерфейса при выборе interaction target, E по Started вместо Triggered,
расширенный E/respawn demo pickup, Jump по Started/Completed и дополнительные
уведомления при HealthMax clamp. Для строгого паритета каждое решение согласовывать отдельно.

Приоритет: закончить blackhole → teleport и две дополнительные атаки → damage sense,
ragdoll и hit feedback → полный AI/MonsterData → HUD/AnimInstance → director и итоговая карта.


## ProjectileBlackhole — проверено в PIE

RogueProjectileBlackhole наследует RogueProjectile на daScript. Новый параметр
CollisionProfile у базового снаряда сохраняет Projectile по умолчанию и позволяет
blackhole использовать BlackholeCore из исходного DefaultEngine.ini 992f860.
Сохранены скорость 500, lifespan 5, ядро 20 и постоянная radial force -800000
в радиусе 1200 с исключением канала Pawn. Родительский hit не срабатывает при
прохождении мира; физические PhysicsBody-акторы поглощаются через native overlap.

Адаптация удаления: коллизия поглощённого актора отключается сразу, а удаление
планируется через native lifespan с задержкой 1 мс. Это сохраняет однократное
поглощение и позволяет выполнить чужой EndPlay вне текущего script callback.
GenerateOverlapEvents включается перед запуском в BeginPlay. Видимая неподвижная
RogueBlackholeDemo находится отдельно в roguedemo. Карта — BlackholeTest.
Все восемь групп rogue-blackhole-v7-20261104 прошли с проверкой журнала и teardown.
Следующий класс этапа 2 — RogueProjectileTeleport.


## Движение игрока — сверено с Blueprint 4 ноября 2026

Исправлена камера и ориентация: bUseControllerRotationYaw=true,
bOrientRotationToMovement=false, bUseControllerDesiredRotation=false.
Корпус смотрит по yaw камеры; S не разворачивает его назад, A/D дают стрейф.
WalkSpeed=550, JumpZVelocity=420, AirControl=0.05, RotationRate.Yaw=360.
SpringArm: TargetArmLength=175, RelativeLocation.Z=80, SocketOffset.Y=80.
Эти значения взяты из исходного BP_PlayerCharacter 992f860.

Пункт прежнего аудита о скорости игрока 450 закрыт. Скорость AI=450 и урон=51
также подтверждены и перенесены в последующем этапе боевого паритета. Подготовка персонажа использует
автоматический Reimport, сохраняя ручные overrides. Движение, спринт и связанные
проверки стрельбы прошли реальный PIE; подробности в VALIDATION.md.

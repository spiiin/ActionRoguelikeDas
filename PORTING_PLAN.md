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

Статус на 2 ноября 2026: RogueProjectile и демонстрационный запуск по ЛКМ реализованы на daScript и проходят целевой PIE-тест. Остальные классы этапа ещё не перенесены.

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

## Текущее состояние

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

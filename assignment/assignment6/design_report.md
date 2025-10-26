# Design Report

## References
- https://geeksforgeeks.org for definition review of each pattern

## Creational Patterns
### Instantiating Instrument Types - Factory Pattern
The Factory pattern defines an interface for the creation of objects, and lets subclasses decide which specific object to instantiate


**Rationale**: Callers are decoupled from the concrete instrument types. They just need to load the data, and let the factory create an appropriate instrument type object without caring about the details. Furthermore, it is also extensible and we can easily add new instruments over time.

**Tradeoff**: Extra layers to debug from caller, to factory, to builder class. Also, we risk factory bloat, the factory being a 'god' object with huge if/elif trees deciding dozens of types and sub-types. This might cause merge conflicts and bug spikes, and we can't unit-test types in isolation, all checks have to be done.

### Centralizing system configuration - Singleton Pattern
Singleton Design Pattern ensures that for a class, there will only be one instance of it. And it also provides a global access point to it.

**Rationale**: Considering we want to centralize these configurations, a singleton directly lets us do this with its single source of truth. There is also coordinated behaviour, that lets us apply any changes across globally.

**Tradeoff**: Concurrency hazards such as race conditions so we have to implement thread-safety.

### Constructing complex portfolios with nested positions and metadata using a builder pattern
The Builder design pattern gives a step-by-step approach to constructing objects, separating the creation process from the object's representation itself. This allows us to create different variations of an object using a common method.

**Rationale:** Provides us with stepwise construction, allowing us to add names, positions, owners, etc fluently. 

**Tradeoff:** If we use a mutable state like a list or dict, continuing with the same builder instance, the state can 'leak' into the next build. Additional code abstractions.

## Structural Patterns
### Adding analytics to instruments using Decorator Pattern wihtout modifying base class
Decorator patterns lets us wrap concrete objects, such that we give it attributes without changing that of objets of the same class.

**Rationale:** Instead of modifying the base code, we can easily create new wrappers to get various metrics. Concerns are separated, whereby time-series math is in `Instrument` while market data is in the decorators. We also only pay for the metrics we choose to wrap. `Instrument` itself stays cheap. We can also unit-test each metric in isolation like this.

**Tradeoff:** Each `get_metrics()` will refilter and sort the same data, making us recompute it a few times unless we cache. Need to also be aware that decorated objects require `market_data` and `benchmark`, but that isn't visible from base type so we just have to know beforehand. Debugging also might become harder as a stack gets larger, making it less obvious which layer misaligned returns or produces NaN values. 

### Model portfolios as trees of positions and sub-portfolios using Composite Pattern
Composite patterns organises objects to follow a tree structure, such that we can treat specific objects, or groups of them, uniformly.

**Rationale:** Portfolios follow a natural hierarchy that maps exactly to a tree. Portfolios -> Sleeves -> Sub-sleeves -> Positions. Traversals are the business logic. Treating a single `Position` as a leaf and `PortfolioGroup` as a composite the same, both answer `get_value()` and `get_positions()` which make recursive operations such as PnL trivial. Adding new node types is also easy without changing callers, just by calling the common interface.

**Tradeoff:** Operations like `get_value()` will walk the tree everytime, hence O(n). Same `Position` being added to multiple groups might leak data if its mutable. Some methods also only make sense on composites instead of leaves, such as `add()`, and vice versa. Deep nesting can lead to recursion limits being hit, so might need to consider iterative traversals.

### Standardize external data formats into MarketDataPoints objects using Adapter Pattern
Acts as a bridge to link 2 incompatible interfaces so they can work together. 

**Rationale:** No matter the source, we structure it into `MarketDataPoint`. We can simply adapt new data sources just by writing a small adapter. We can also clean up messy data this way for each source before it touches our system. Easy to test too as each adapter can be checked with tiny sample files.

**Tradeoff:** Extra layer between data and our code, more things to read while debugging. Have to rewrite code if source changes their format. By standardising, some extra fields may be left out. 

## Behavioural Patterns

### Support interchangeable trading strategies using Strategy Pattern
Allows us to define a family of algorithms or behaviours, put them in their own class, and make them interchangeable at runtime. Useful in changing behaviour of a class without touching its code

**Rationale:** Everything calls the same method `get_signals()` so its easy to swap rules. Clearly separates data I/O and risk checks from trading rule. Makes each strategy easily checkable too with some data, one rule at a time. Grows cleanly too when adding a new trading strategy. Add a new class instead of editing a big pile of if/else statements. 

**Tradeoff:** Multiple classes instead of one function, so more code to manage.  

### Notify external modules when signals are generated using Observer Pattern
"Subscribe and notify" setup where the publisher does its job, and when something happens, it notifies everyone who signed up to hear about it i.e. the subscribers. 

**Rationale:** When a strategy emits a signal, different modules that subscribe to it such as logging and metrics can react automatically, with no edits to the strategy. No need to touch any of this code, if something else needs to use the signals we can simply extend to a new observer. Each piece stays focused and works on their goal

**Tradeoff:** Listeners run in the order they are attached, needs management. A slow observer will stall `notify()`. Need to keep track of detachments to avoid unnecessary sending of signals to observers who dont need it. 

### Encapsulate Order Execution and support undo/redo using Command Pattern
Way to wrap actions as objects such that instead of calling an action, we make it into an object that has 2 buttons. `execute()` and `undo()`.

**Rationale:** One clear button for each command, the caller doesn't need to know how positions/cash are updated. Built-in undo/redo helps in backing out from mistakes, then re-apply them with the invoker's stacks. Also safer sequencing as the invoker will keep history in order and we dont accidentally redo out of sequence. New actions, such as maybe amend, become new command classes without touching the invoker or context. 

**Tradeoff:** More moving parts to manage. There's also performance/latency overhead for logging and stack memory growth as undo/redo stacks grow over time unless we bound or snapshot them. 

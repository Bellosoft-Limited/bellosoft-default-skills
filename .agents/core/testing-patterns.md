# Testing Patterns & TDD
> Sources: Microsoft .NET Unit Testing Best Practices, Microsoft ASP.NET Core Integration Testing, xUnit docs
> Frameworks: xUnit · Moq/NSubstitute · WebApplicationFactory · Playwright

---

## TDD Cycle (Red-Green-Refactor)

- **RED**: Write a failing test first. The test defines the expected behavior before any implementation exists.
- **GREEN**: Write the minimum production code to make the test pass. No extra code.
- **REFACTOR**: Clean up the code while keeping all tests green. Improve design, naming, duplication.

Rule: Never write production code without a failing test. Never write more production code than needed to pass the current failing test.

---

## Unit Test Characteristics (FIRST)

- **Fast** — Each test runs in milliseconds. Thousands of tests complete in seconds.
- **Isolated** — No dependencies on databases, file systems, network, or other tests.
- **Repeatable** — Same result every time, regardless of environment or execution order.
- **Self-Checking** — The test runner determines pass/fail automatically. No manual inspection.
- **Timely** — Written close to the production code, ideally before it (TDD).

---

## Test Structure: Arrange-Act-Assert (AAA)

Every test must follow this pattern with blank-line separation:

```csharp
[Fact]
public void Add_EmptyString_ReturnsZero()
{
    // Arrange
    var calculator = new StringCalculator();

    // Act
    var result = calculator.Add("");

    // Assert
    Assert.Equal(0, result);
}
```

- Never merge Act and Assert. Never skip the Act section.
- Use comments to label the three sections.

---

## Naming Convention

Format: `{MethodName}_{Scenario}_{ExpectedBehavior}`

| Good | Bad |
|---|---|
| `Add_SingleNumber_ReturnsSameNumber` | `Test1` |
| `GetOrder_InvalidId_ThrowsNotFoundException` | `TestGetOrder` |
| `DeleteUser_NullUser_ThrowsArgumentNullException` | `DeleteUserTest` |

---

## What to Test

- **Public API surface** only. Do not test private methods — test through the public methods that call them.
- **Boundary conditions**: empty input, null values, max/min values, overflow.
- **Error paths**: expected exceptions, unauthorized access, validation failures.
- **Happy paths**: the expected successful flow.

---

## xUnit Conventions

- Use `[Fact]` for single-input tests. Use `[Theory]` with `[InlineData]` for parameterized tests.
- Constructor is the setup mechanism (replaces `[Setup]` from other frameworks).
- Implement `IClassFixture<T>` for shared context, `ICollectionFixture<T>` for collection-level shared state.
- `IDisposable` for teardown. Do not use `[TearDown]` attributes.
- Test projects require: `Microsoft.NET.Test.Sdk`, `xunit`, `xunit.runner.visualstudio` packages.

---

## Parameterized Tests (Theory)

Use `[Theory]` to test multiple inputs without duplicating code:

```csharp
[Theory]
[InlineData("", 0)]
[InlineData("1", 1)]
[InlineData("1,2", 3)]
public void Add_VariousInputs_ReturnsExpectedSum(string input, int expected)
{
    var calculator = new StringCalculator();
    var result = calculator.Add(input);
    Assert.Equal(expected, result);
}
```

Never use loops (`for`, `foreach`) inside a single test. Use `[Theory]`/`[InlineData]` instead.

---

## Mocks, Stubs, and Fakes Terminology

- **Fake**: A generic test double. Can be a stub or a mock.
- **Stub**: Provides controlled values to the system under test. Assertions are NOT made on stubs.
- **Mock**: A fake that is asserted against (e.g., verifying a method was called).

```csharp
// Stub — used only to provide data, not asserted
var stubRepo = new Mock<IOrderRepository>();
stubRepo.Setup(r => r.GetById(1)).Returns(new Order { Id = 1 });

// Mock — asserted after the action
var mockLogger = new Mock<ILogger>();
service.Process(order);
mockLogger.Verify(l => l.Log(It.IsAny<string>()), Times.Once);
```

---

## Mocking Frameworks

- Use **Moq** or **NSubstitute** — both are industry standard for .NET.
- Use strict mocking only for critical behaviors. Prefer loose (default) mocks.

```csharp
// Moq
var mock = new Mock<IService>();
mock.Setup(s => s.GetData()).Returns(new List<string>());

// NSubstitute
var substitute = Substitute.For<IService>();
substitute.GetData().Returns(new List<string>());
```

- Replace `DateTime.Now`, `Guid.NewGuid()`, `Random` with abstractions (`IDateTimeProvider`, `IGuidFactory`) to make code testable.

---

## ASP.NET Core Integration Testing

- Use `Microsoft.AspNetCore.Mvc.Testing` package — provides `WebApplicationFactory<TEntryPoint>`.
- Reference the SUT project (`<ProjectReference>`).
- Override services in tests with `ConfigureTestServices`.
- Use SQLite in-memory or the EF Core in-memory provider — prefer SQLite for EF-close fidelity.

```csharp
public class CustomWebApplicationFactory<TProgram>
    : WebApplicationFactory<TProgram> where TProgram : class
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureTestServices(services =>
        {
            services.AddScoped<IQuoteService, TestQuoteService>();
        });
    }
}
```

- Separate integration tests from unit tests in different projects.
- Test HTTP endpoints with `HttpClient` from `CreateClient()`:

```csharp
[Fact]
public async Task Get_Endpoints_ReturnSuccess()
{
    var client = _factory.CreateClient();
    var response = await client.GetAsync("/api/orders");
    response.EnsureSuccessStatusCode();
}
```

---

## Seeding Test Data

- Seed the database in the test setup, not in production code.
- Use a dedicated `Utilities` helper class with `InitializeDbForTests()` and `ReinitializeDbForTests()`.
- Each test should reset data to a known state — never depend on test execution order.

---

## What to Avoid in Tests

- **Magic strings / hard-coded values without explanation**. Use constants.
- **Logic in tests**: no `if`, `while`, `for`, `switch` in test methods.
- **Multiple Act tasks per test**: each test should Act once. Use parameterized tests for variants.
- **Dependencies on infrastructure** (database, file system, network) in unit tests — use mocks.
- **Setup/Teardown attributes** (like `[Setup]`) — use constructor and helper methods instead.
- **Testing implementation details**: test behavior, not internal structure.
- **Shared mutable state between tests**: tests must not depend on each other.

---

## Code Coverage

- Aim for meaningful coverage, not a specific percentage. 80% is a common goal.
- Cover all branches and error paths. Do not pad coverage with trivial tests.
- Use `dotnet test --collect:"XPlat Code Coverage"` for coverage reports.
- Never gate the build on a coverage percentage — it invites padding, not quality.

---

## TDD Workflow (Step by Step)

1. Write a failing test (RED).
2. Run the test — confirm it fails with the expected message.
3. Write the minimum production code to make it pass (GREEN).
4. Run all tests — confirm all pass.
5. Refactor production code and tests (REFACTOR).
6. Run all tests again — confirm still green.
7. Commit.

---

## What to Never Do

- Never write production code before its test in a TDD workflow.
- Never merge a PR if any tests are failing.
- Never share state between tests (no static test data).
- Never include integration test projects in the unit test run.
- Never use `Thread.Sleep` or `Task.Delay` for test synchronization.
- Never test private/internal methods directly — test through public API.
- Never use `[Fact]` when the test body contains loops — use `[Theory]`.
- Never mock types you don't own.

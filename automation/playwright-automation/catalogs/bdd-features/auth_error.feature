Feature: Identity service unavailable (Authentication)
  Nexora page behavior mapped to Keycloak OIDC availability state.

  Scenario: NX-BDD-044 Identity service unavailable: the identity provider is unavailable
    Given a visitor is on the Nexora account lifecycle
    When the identity provider is unavailable
    Then a clear service error and retry action are shown
    And the result is consistent with Keycloak OIDC availability state and the configured identity/session state

  Scenario: NX-BDD-092 Identity service unavailable: the identity provider becomes available
    Given a visitor is on the Nexora account lifecycle
    When the identity provider becomes available
    Then retry reloads the authentication check
    And the result is consistent with Keycloak OIDC availability state and the configured identity/session state

  Scenario: NX-BDD-140 Identity service unavailable: the identity provider remains unavailable after retry
    Given a visitor is on the Nexora account lifecycle
    When the identity provider remains unavailable after retry
    Then the error remains visible and the visitor stays signed out
    And the result is consistent with Keycloak OIDC availability state and the configured identity/session state

  Scenario: NX-BDD-188 Identity service unavailable: the identity provider recovers after a failed attempt
    Given a visitor is on the Nexora account lifecycle
    When the identity provider recovers after a failed attempt
    Then retry reaches the sign-in screen
    And the result is consistent with Keycloak OIDC availability state and the configured identity/session state

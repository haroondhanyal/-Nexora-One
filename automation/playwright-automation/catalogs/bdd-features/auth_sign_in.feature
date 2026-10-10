Feature: Sign in (Authentication)
  Nexora page behavior mapped to Keycloak OIDC sign-in; local demo owner in local-demo mode.

  Scenario: NX-BDD-045 Sign in: an owner selects secure sign-in
    Given a visitor is on the Nexora account lifecycle
    When an owner selects secure sign-in
    Then the browser starts the configured Keycloak OIDC flow
    And the result is consistent with Keycloak OIDC sign-in; local demo owner in local-demo mode and the configured identity/session state

  Scenario: NX-BDD-093 Sign in: a local demo owner selects continue
    Given a visitor is on the Nexora account lifecycle
    When a local demo owner selects continue
    Then the local demo workspace opens without requesting a password
    And the result is consistent with Keycloak OIDC sign-in; local demo owner in local-demo mode and the configured identity/session state

  Scenario: NX-BDD-141 Sign in: a visitor selects forgot password
    Given a visitor is on the Nexora account lifecycle
    When a visitor selects forgot password
    Then the configured identity-provider reset flow opens
    And the result is consistent with Keycloak OIDC sign-in; local demo owner in local-demo mode and the configured identity/session state

  Scenario: NX-BDD-189 Sign in: a visitor selects sign-up
    Given a visitor is on the Nexora account lifecycle
    When a visitor selects sign-up
    Then the configured identity-provider registration flow opens
    And the result is consistent with Keycloak OIDC sign-in; local demo owner in local-demo mode and the configured identity/session state

Feature: Loading and session check (Authentication)
  Nexora page behavior mapped to Client session and Keycloak OIDC initialization.

  Scenario: NX-BDD-043 Loading and session check: a visitor opens Nexora One
    Given a visitor is on the Nexora account lifecycle
    When a visitor opens Nexora One
    Then the branded loading state appears while session status is checked
    And the result is consistent with Client session and Keycloak OIDC initialization and the configured identity/session state

  Scenario: NX-BDD-091 Loading and session check: the identity session is valid
    Given a visitor is on the Nexora account lifecycle
    When the identity session is valid
    Then the visitor is routed to their authorized workspace
    And the result is consistent with Client session and Keycloak OIDC initialization and the configured identity/session state

  Scenario: NX-BDD-139 Loading and session check: the identity session is absent
    Given a visitor is on the Nexora account lifecycle
    When the identity session is absent
    Then the sign-in screen appears after initialization
    And the result is consistent with Client session and Keycloak OIDC initialization and the configured identity/session state

  Scenario: NX-BDD-187 Loading and session check: the session check is still pending
    Given a visitor is on the Nexora account lifecycle
    When the session check is still pending
    Then the loading progress remains visible without flashing private content
    And the result is consistent with Client session and Keycloak OIDC initialization and the configured identity/session state

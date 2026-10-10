import { ScreenPage } from './screen-page.js';

export class AuthSignUpPage extends ScreenPage {
  constructor(page) { super(page, "auth_sign_up"); }

  get identityProviderForm() { return this.locator("identityProviderForm"); }
  get username() { return this.locator("username"); }
  get email() { return this.locator("email"); }
  get password() { return this.locator("password"); }
  get visiblePassword() { return this.locator("visiblePassword"); }
  get submit() { return this.locator("submit"); }
  get tableCells() { return this.page.getByRole("cell"); }
}

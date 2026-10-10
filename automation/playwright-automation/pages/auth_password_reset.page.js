import { ScreenPage } from './screen-page.js';

export class AuthPasswordResetPage extends ScreenPage {
  constructor(page) { super(page, "auth_password_reset"); }

  get identityProviderForm() { return this.locator("identityProviderForm"); }
  get email() { return this.locator("email"); }
  get submit() { return this.locator("submit"); }
  get tableCells() { return this.page.getByRole("cell"); }
}

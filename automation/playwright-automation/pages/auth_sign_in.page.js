import { ScreenPage } from './screen-page.js';

export class AuthSignInPage extends ScreenPage {
  constructor(page) { super(page, "auth_sign_in"); }

  get pageTitle() { return this.locator("pageTitle"); }
  get signInButton() { return this.locator("signInButton"); }
  get resetPasswordLink() { return this.locator("resetPasswordLink"); }
  get signUpButton() { return this.locator("signUpButton"); }
  get localDemoNote() { return this.locator("localDemoNote"); }
  get tableCells() { return this.page.getByRole("cell"); }
}

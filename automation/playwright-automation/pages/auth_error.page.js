import { ScreenPage } from './screen-page.js';

export class AuthErrorPage extends ScreenPage {
  constructor(page) { super(page, "auth_error"); }

  get brandMark() { return this.locator("brandMark"); }
  get errorMessage() { return this.locator("errorMessage"); }
  get retryButton() { return this.locator("retryButton"); }
  get tableCells() { return this.page.getByRole("cell"); }
}

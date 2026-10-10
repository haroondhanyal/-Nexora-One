import { ScreenPage } from './screen-page.js';

export class AuthLoadingPage extends ScreenPage {
  constructor(page) { super(page, "auth_loading"); }

  get brandMark() { return this.locator("brandMark"); }
  get pageTitle() { return this.locator("pageTitle"); }
  get progress() { return this.locator("progress"); }
  get tableCells() { return this.page.getByRole("cell"); }
}

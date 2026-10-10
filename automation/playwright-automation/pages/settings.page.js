import { ScreenPage } from './screen-page.js';

export class SettingsPage extends ScreenPage {
  constructor(page) { super(page, "settings"); }

  get pageHeading() { return this.locator("pageHeading"); }
  get sidebarItem() { return this.locator("sidebarItem"); }
  get primaryContent() { return this.locator("primaryContent"); }
  get globalSearch() { return this.locator("globalSearch"); }
  get workspaceSwitcher() { return this.locator("workspaceSwitcher"); }
  get table() { return this.locator("table"); }
  get tableHeader() { return this.locator("tableHeader"); }
  get tableRows() { return this.locator("tableRows"); }
  get primaryAction() { return this.locator("primaryAction"); }
  get form() { return this.locator("form"); }
  get validation() { return this.locator("validation"); }
  get tableCells() { return this.page.getByRole("cell"); }
}

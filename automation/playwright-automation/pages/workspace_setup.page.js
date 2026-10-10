import { ScreenPage } from './screen-page.js';

export class WorkspaceSetupPage extends ScreenPage {
  constructor(page) { super(page, "workspace_setup"); }

  get pageTitle() { return this.locator("pageTitle"); }
  get companyName() { return this.locator("companyName"); }
  get industryOptions() { return this.locator("industryOptions"); }
  get createWorkspaceButton() { return this.locator("createWorkspaceButton"); }
  get validation() { return this.locator("validation"); }
  get tableCells() { return this.page.getByRole("cell"); }
}

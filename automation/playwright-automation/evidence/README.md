# Hard case evidence

Copy reviewed screenshots (`.png`, `.jpg`, `.webp`) and recordings (`.webm`, `.mp4`) into this directory. Include the case ID in each filename, for example `NX-API-042-wrong-tenant.webm`.

Run `npm --prefix automation/playwright-automation run build:catalog` to refresh the evidence gallery. Failed Playwright tests retain their screenshot, video, and trace under `test-results/`; copy the selected evidence here when it should appear in the QA report center.

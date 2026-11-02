# Project X Guide publication

This is the dedicated PUBLIC publication repository requested by Andy on 2026-11-02. It is separate from the private Reference/PXNO/TTI/ARES controls. Never change those repositories' visibility or mirror their contents here.

Only own, rights-cleared guides with exact-hash release approval and current-build runtime evidence may be published. The request to create this repository is NOT approval of any existing draft. Never fabricate tests or automatically change approval/test status after a DCS patch.

Keep the download URL stable. New eligible catalog entries and release assets must update the site automatically. Preserve old immutable releases as archive. Do not replace or delete release files to make a hash match.

Read PUBLISHING.md before preparing a release. Public evidence must exclude local paths, credentials, private-source extracts and unapproved third-party images. Keep approved binaries in GitHub Releases, not in the Git source tree. No binary original from the shared reference library belongs here.

Keep the local working master in the established Project-X storage location documented in the private handoff. Do not publish that local path here. Temporary tool directories are not masters. Tests and website previews do not constitute a DCS test.

Run python -m unittest discover -s tests before publication changes. Verify the deployed website and status.json after the workflow succeeds. All browser-visible compatibility claims must name the tested DCS build and the last successful official-version query.

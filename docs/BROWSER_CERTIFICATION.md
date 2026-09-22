# Browser, Accessibility and Frontend Security Certification — P37

P37 preserves the P36 dependency-certification correction unchanged: the repository-root `package-lock.json` remains a runner-generated dependency-resolution artifact excluded from the application-source fingerprint, while its SHA-256/version and exact root/workspace manifest consistency are mandatory dependency evidence. The P37 change is confined to staging child-result classification and does not alter browser, Playwright or axe requirements.

import {defineConfig} from '@playwright/test';
import base from './playwright.config';
// Recording every action adds DOM snapshots/video work to the measured CPU window.
// Functional suites keep their evidence capture; performance checks take an image after measurement.
export default defineConfig({...base,testMatch:['blockchain-background-performance.spec.ts'],workers:1,retries:0,timeout:60000,use:{...base.use,trace:'off',video:'off'}});

import {defineConfig} from '@playwright/test';
import base from './playwright.config';
export default defineConfig({...base,testMatch:['blockchain-background-performance.spec.ts'],workers:1,retries:0,timeout:60000});

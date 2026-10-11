import {test,expect} from '@playwright/test';

test('actual production draws Risk Atlas, pauses, changes chapters and keeps healthy account gates',async({page})=>{
 await page.setViewportSize({width:1440,height:900});const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.locator('meta[name="rivexis-build"]')).toHaveAttribute('content',process.env.RIVEXIS_EXPECTED_BUILD_SHA!);
 await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');await expect(page.locator('.atlasEnvironment')).toHaveAttribute('data-renderer','webgl');
 await page.getByRole('button',{name:'Pause motion',exact:true}).click();await expect(page.locator('.atlasEnvironment')).toHaveAttribute('data-motion','paused');
 await page.getByRole('button',{name:'Alternatives',exact:true}).click();await expect(page.locator('.atlasDescription')).toContainText('Available capital creates');
 await page.getByRole('button',{name:'Resume motion',exact:true}).click();await expect(page.locator('.atlasEnvironment')).toHaveAttribute('data-motion','running');
 await page.mouse.wheel(0,100);await page.locator('.gasShowcase').scrollIntoViewIfNeeded();await expect(page.locator('main')).toHaveAttribute('data-atlas-chapter','3');
 await page.goto('/');await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');await page.screenshot({path:'../../../../outputs/risk-atlas-live-desktop.png'});
 await expect(page.getByTestId('service-availability')).toHaveCount(0);expect(errors).toEqual([]);
});

test('actual production reduced-motion and mobile views retain meaningful vector controls',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','vector');
 await page.getByRole('button',{name:'Transaction',exact:true}).click();await expect(page.locator('.atlasVectorPaths circle')).toHaveCount(4);
 await page.getByRole('button',{name:'Alternatives',exact:true}).click();await expect(page.locator('.atlasVectorPaths path')).toHaveCount(3);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../../../outputs/risk-atlas-live-mobile.png'});
 await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:1440,height:900});await expect(page.getByRole('button',{name:'Static view',exact:true})).toBeDisabled();await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','vector');
});

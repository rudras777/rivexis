import type {ButtonHTMLAttributes,ReactNode} from 'react';
const variants={primary:'button',secondary:'ghost',tertiary:'textButton',critical:'criticalButton',icon:'iconButton'} as const;
export function ActionButton({variant='primary',loading=false,children,className='',disabled,...props}:ButtonHTMLAttributes<HTMLButtonElement>&{variant?:keyof typeof variants;loading?:boolean;children:ReactNode}){return <button type="button" {...props} className={`${variants[variant]} ${className}`} disabled={disabled||loading} aria-busy={loading||undefined}>{children}</button>}

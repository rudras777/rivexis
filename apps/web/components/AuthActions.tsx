"use client";
import Link from "next/link";
import {useQuery} from "@tanstack/react-query";
import {api} from "@/lib/api";
import {authHref} from "@/lib/auth-destination";
export function usePublicSession(){return useQuery({queryKey:["public-session"],queryFn:()=>api<{authenticated:boolean;email_verified:boolean}>("/api/v1/auth/session-status"),retry:false,staleTime:30_000,refetchOnWindowFocus:false});}
export function AuthActions({destination="/workspace",signupLabel="Sign up"}:{destination?:string;signupLabel?:string}){
  const q=usePublicSession(),signedIn=!!q.data?.authenticated&&q.data.email_verified;
  return <div className="authActions"><Link className="ghost" href={authHref("/login",destination)}>Log in</Link><Link className="button" href={signedIn?destination:authHref("/signup",destination)}>{signedIn?"Open dashboard":signupLabel}<span aria-hidden="true">↗</span></Link></div>;
}
export function FeatureLink({destination,children,className="textButton"}:{destination:string;children:React.ReactNode;className?:string}){
  const q=usePublicSession();return <Link className={className} href={q.data?.authenticated&&q.data.email_verified?destination:authHref("/login",destination)}>{children}</Link>;
}

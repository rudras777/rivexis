"use client";

import Link from "next/link";
import {useDeFi} from "@/components/DeFiContext";
import {useQueryClient} from "@tanstack/react-query";
import {useEffect,useState} from "react";
import {useForm} from "react-hook-form";
import {authHref,intendedDestination} from "@/lib/auth-destination";
import {useRouter} from "next/navigation";
import {AuthFrame} from "@/components/AuthFrame";
import {api,setCsrfToken} from "@/lib/api";
import {readDeviceHint,removeDeviceHint} from "@/lib/browser-storage.mjs";

type EmailForm={email:string};
type CodeForm={token:string};

export default function VerifyEmail(){
  const emailForm=useForm<EmailForm>();
  const codeForm=useForm<CodeForm>();
  const [notice,setNotice]=useState("");
  const [error,setError]=useState("");
  const [destination,setDestination]=useState("/workspace");
  const router=useRouter();
  const queryClient=useQueryClient();const risk=useDeFi();

  useEffect(()=>{
    setDestination(intendedDestination());
    const pending=readDeviceHint('session',"rivexis_pending_verification_email");
    if(pending)emailForm.setValue("email",pending);
    if(new URLSearchParams(window.location.search).get("sent")==="1")setNotice("Verification email requested. Open its confirmation link, then log in. Check your spam folder if it has not arrived.");
  },[emailForm]);

  async function resend(v:EmailForm){
    try{
      setError("");
      await api<{status:string}>("/api/v1/auth/email-verification/request",{method:"POST",body:JSON.stringify(v)});
      setNotice("Verification request received. If your account is eligible, open the confirmation link in your email, then log in. Delivery may take a few minutes; check your spam folder too.");
    }catch{
      setError("Verification email is temporarily unavailable. Try again shortly.");
    }
  }

  async function confirm(v:CodeForm){
    try{
      setError("");
      const email=emailForm.getValues("email")||readDeviceHint('session',"rivexis_pending_verification_email")||"";
      const result=await api<{status:string;authenticated?:boolean;csrf_token?:string}>("/api/v1/auth/email-verification/confirm",{method:"POST",body:JSON.stringify({...v,email})});
      removeDeviceHint('session',"rivexis_pending_verification_email");
      const destination=intendedDestination();
      if(result.authenticated&&result.csrf_token){
        setCsrfToken(result.csrf_token);
        risk.reset();
      await queryClient.cancelQueries({queryKey:["account-settings"]});queryClient.removeQueries({queryKey:["account-settings"]});
      await queryClient.invalidateQueries({queryKey:["public-session"]});
        removeDeviceHint('session',"rivexis_pending_destination");
        router.replace(destination);
      }else router.replace(authHref("/login",destination,{verified:"1"}));
    }catch{
      setError("This verification code is invalid or expired. Request a new one.");
    }
  }

  return <AuthFrame mode="verification">
      <h1>Verify your email</h1>
      <p>Open the confirmation link in your Rivexis email, then return to log in. Check your spam folder too. Never share a verification link or code.</p>
      <p className="authNote"><Link href={authHref("/login",destination)}>Continue to login</Link>.</p>
      {notice&&<div className="success" role="status">{notice}</div>}
      <form className="form" method="post" onSubmit={codeForm.handleSubmit(confirm)}>
        <label className="field">Verification code<input type="text" autoComplete="one-time-code" required aria-describedby="verification-code-help" {...codeForm.register("token")}/></label>
        <p id="verification-code-help" className="authNote">Use this only if your email includes a code. A confirmation link works without entering a code here.</p>
        <button className="button" type="submit" disabled={codeForm.formState.isSubmitting}>{codeForm.formState.isSubmitting?"Verifying…":"Verify account"}</button>
      </form>
      <form className="form secondaryForm" method="post" onSubmit={emailForm.handleSubmit(resend)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...emailForm.register("email")}/></label>
        <button className="ghost" type="submit" disabled={emailForm.formState.isSubmitting}>{emailForm.formState.isSubmitting?"Sending…":"Send verification email"}</button>
      </form>
      {error&&<div className="error authFlowError" role="alert">{error}</div>}
      <p className="authNote"><Link href="/login">Return to login</Link>.</p>
  </AuthFrame>;
}

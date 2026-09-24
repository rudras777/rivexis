"use client";

import Link from "next/link";
import {useEffect,useState} from "react";
import {useForm} from "react-hook-form";
import {useRouter} from "next/navigation";
import {Brand} from "@/components/Brand";
import {api} from "@/lib/api";

type EmailForm={email:string};
type CodeForm={token:string};

export default function VerifyEmail(){
  const emailForm=useForm<EmailForm>();
  const codeForm=useForm<CodeForm>();
  const [notice,setNotice]=useState("");
  const [error,setError]=useState("");
  const router=useRouter();

  useEffect(()=>{
    const pending=sessionStorage.getItem("rivexis_pending_verification_email");
    if(pending)emailForm.setValue("email",pending);
    if(new URLSearchParams(window.location.search).get("sent")==="1")setNotice("Verification email requested. Enter the code from your inbox.");
  },[emailForm]);

  async function resend(v:EmailForm){
    try{
      setError("");
      await api<{status:string}>("/api/v1/auth/email-verification/request",{method:"POST",body:JSON.stringify(v)});
      setNotice("If the account is eligible, a new verification code has been sent.");
    }catch{
      setError("Verification email is temporarily unavailable. Try again shortly.");
    }
  }

  async function confirm(v:CodeForm){
    try{
      setError("");
      await api<{status:string}>("/api/v1/auth/email-verification/confirm",{method:"POST",body:JSON.stringify(v)});
      sessionStorage.removeItem("rivexis_pending_verification_email");
      router.replace("/login?verified=1");
    }catch{
      setError("This verification code is invalid or expired. Request a new one.");
    }
  }

  return <main className="formPage">
    <section className="formCard">
      <Brand/>
      <h1>Verify your email</h1>
      <p>Enter the one-time code from Rivexis. Never share this code with another person.</p>
      {notice&&<div className="success" role="status">{notice}</div>}
      <form className="form" onSubmit={codeForm.handleSubmit(confirm)}>
        <label className="field">Verification code<input type="text" autoComplete="one-time-code" required {...codeForm.register("token")}/></label>
        <button className="button" disabled={codeForm.formState.isSubmitting}>{codeForm.formState.isSubmitting?"Verifying…":"Verify account"}</button>
      </form>
      <form className="form secondaryForm" onSubmit={emailForm.handleSubmit(resend)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...emailForm.register("email")}/></label>
        <button className="ghost" disabled={emailForm.formState.isSubmitting}>{emailForm.formState.isSubmitting?"Sending…":"Send a new code"}</button>
      </form>
      {error&&<div className="error authFlowError" role="alert">{error}</div>}
      <p className="authNote"><Link href="/login">Return to login</Link>.</p>
    </section>
  </main>;
}

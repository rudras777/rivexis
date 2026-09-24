"use client";

import Link from "next/link";
import {useEffect,useState} from "react";
import {useForm} from "react-hook-form";
import {useRouter} from "next/navigation";
import {Brand} from "@/components/Brand";
import {api,setCsrfToken} from "@/lib/api";
import {authErrorMessage} from "@/lib/auth";

type Form={email:string;password:string};

export default function Login(){
  const {register,handleSubmit,formState:{isSubmitting}}=useForm<Form>();
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const router=useRouter();

  useEffect(()=>{
    if(new URLSearchParams(window.location.search).get("verified")==="1"){
      setNotice("Email verified. Log in to continue.");
    }
  },[]);

  async function submit(v:Form){
    try{
      setError("");
      const r=await api<{csrf_token:string}>("/api/v1/auth/web/login",{
        method:"POST",
        body:JSON.stringify(v),
      });
      setCsrfToken(r.csrf_token);
      router.replace("/workspace");
    }catch(e){
      setError(authErrorMessage(e,"login"));
    }
  }

  return <main className="formPage">
    <section className="formCard">
      <Brand/>
      <h1>Log in</h1>
      <p>Access your Rivexis workspace.</p>
      {notice&&<div className="success" role="status">{notice}</div>}
      <form className="form" onSubmit={handleSubmit(submit)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...register("email")}/></label>
        <label className="field">Password<input type="password" autoComplete="current-password" required minLength={8} {...register("password")}/></label>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" disabled={isSubmitting}>{isSubmitting?"Logging in…":"Log in"}</button>
      </form>
      <p className="authNote"><Link href="/forgot-password">Forgot your password?</Link> <Link href="/verify-email">Verify an existing account</Link>. Need an account? <Link href="/signup">Create one</Link>.</p>
    </section>
  </main>;
}

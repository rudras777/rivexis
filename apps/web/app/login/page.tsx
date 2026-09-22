"use client";

import Link from "next/link";
import {useState} from "react";
import {useForm} from "react-hook-form";
import {useRouter} from "next/navigation";
import {Brand} from "@/components/Brand";
import {api,setCsrfToken} from "@/lib/api";
import {authErrorMessage} from "@/lib/auth";

type Form={email:string;password:string};

export default function Login(){
  const {register,handleSubmit,formState:{isSubmitting}}=useForm<Form>();
  const [error,setError]=useState("");
  const router=useRouter();

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
      <form className="form" onSubmit={handleSubmit(submit)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...register("email")}/></label>
        <label className="field">Password<input type="password" autoComplete="current-password" required minLength={8} {...register("password")}/></label>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" disabled={isSubmitting}>{isSubmitting?"Logging in…":"Log in"}</button>
      </form>
      <p className="authNote">Password recovery is not enabled on this preview. Need an account? <Link href="/signup">Create one</Link>.</p>
    </section>
  </main>;
}

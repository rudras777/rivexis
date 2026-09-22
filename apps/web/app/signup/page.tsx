"use client";

import Link from "next/link";
import {useState} from "react";
import {useForm} from "react-hook-form";
import {useRouter} from "next/navigation";
import {Brand} from "@/components/Brand";
import {api,setCsrfToken} from "@/lib/api";
import {authErrorMessage} from "@/lib/auth";

type Form={email:string;password:string;role:string};

export default function Signup(){
  const {register,handleSubmit,formState:{isSubmitting}}=useForm<Form>({defaultValues:{role:"Individual"}});
  const [error,setError]=useState("");
  const router=useRouter();

  async function submit(v:Form){
    try{
      setError("");
      const r=await api<{csrf_token:string}>("/api/v1/auth/web/signup",{
        method:"POST",
        body:JSON.stringify(v),
      });
      setCsrfToken(r.csrf_token);
      router.replace("/onboarding");
    }catch(e){
      setError(authErrorMessage(e,"signup"));
    }
  }

  return <main className="formPage">
    <section className="formCard">
      <Brand/>
      <h1>Create workspace</h1>
      <p>Choose the role that controls terminology, defaults and reporting depth.</p>
      <form className="form" onSubmit={handleSubmit(submit)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...register("email")}/></label>
        <label className="field">Password<input type="password" autoComplete="new-password" required minLength={8} {...register("password")}/></label>
        <label className="field">Who are you?<select {...register("role")}><option>Individual</option><option>Fund</option><option>Treasury</option><option>Analyst</option></select></label>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" disabled={isSubmitting}>{isSubmitting?"Creating account…":"Continue"}</button>
      </form>
      <p className="authNote">Email verification and recovery are not enabled until the approved delivery path is configured. Already registered? <Link href="/login">Log in</Link>.</p>
    </section>
  </main>;
}

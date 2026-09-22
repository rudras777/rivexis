"use client";

import Link from "next/link";
import {useEffect,useState} from "react";
import {useForm} from "react-hook-form";
import {useRouter} from "next/navigation";
import {useQuery} from "@tanstack/react-query";
import {Brand} from "@/components/Brand";
import {ApiError,api,setActiveWorkspaceId} from "@/lib/api";
import {authErrorMessage} from "@/lib/auth";

type Form={name:string;role:string};
type Workspace={id:string;name:string;role:string};

export default function Onboarding(){
  const {register,handleSubmit,formState:{isSubmitting}}=useForm<Form>({
    defaultValues:{name:"Primary Workspace",role:"Individual"},
  });
  const router=useRouter();
  const [error,setError]=useState("");
  const workspaces=useQuery({
    queryKey:["onboarding-workspaces"],
    queryFn:()=>api<{items:Workspace[]}>("/api/v1/workspaces"),
    retry:false,
  });

  useEffect(()=>{
    const existing=workspaces.data?.items[0];
    if(!existing)return;
    setActiveWorkspaceId(existing.id);
    router.replace("/workspace");
  },[router,workspaces.data]);

  async function reconcileCreatedWorkspace(v:Form){
    try{
      const current=await api<{items:Workspace[]}>("/api/v1/workspaces");
      const existing=current.items.find(w=>w.name===v.name&&w.role===v.role);
      if(!existing)return false;
      setActiveWorkspaceId(existing.id);
      router.replace("/workspace");
      return true;
    }catch{
      return false;
    }
  }

  async function submit(v:Form){
    setError("");
    try{
      await api("/api/v1/me/role",{
        method:"PATCH",
        body:JSON.stringify({role:v.role}),
      });

      try{
        const created=await api<Workspace>("/api/v1/workspaces",{
          method:"POST",
          body:JSON.stringify(v),
        });
        setActiveWorkspaceId(created.id);
        router.replace("/workspace");
      }catch(createError){
        if(await reconcileCreatedWorkspace(v))return;
        throw createError;
      }
    }catch(e){
      setError(authErrorMessage(e,"onboarding"));
    }
  }

  if(workspaces.isPending){
    return <main className="formPage"><section className="formCard" role="status" aria-live="polite"><Brand/><h1>Preparing workspace setup</h1><p>Verifying your session and existing workspace state.</p></section></main>;
  }

  if(workspaces.isError){
    const status=workspaces.error instanceof ApiError?workspaces.error.status:null;
    return <main className="formPage"><section className="formCard">
      <Brand/>
      <h1>{status===401?"Session ended":"Workspace setup unavailable"}</h1>
      <p>{authErrorMessage(workspaces.error,"onboarding")}</p>
      <div className="shellStateActions">
        {status===401?<Link className="button" href="/login">Log in again</Link>:<button className="button" type="button" onClick={()=>void workspaces.refetch()} disabled={workspaces.isFetching}>{workspaces.isFetching?"Retrying…":"Retry"}</button>}
        <Link className="ghost" href="/">Public site</Link>
      </div>
    </section></main>;
  }

  if(workspaces.data.items.length){
    return <main className="formPage"><section className="formCard" role="status" aria-live="polite"><Brand/><h1>Opening workspace</h1><p>An existing authorized workspace was found. Rivexis is continuing there instead of creating a duplicate.</p></section></main>;
  }

  return <main className="formPage">
    <section className="formCard">
      <Brand/>
      <h1>Configure workspace</h1>
      <p>Your role changes defaults and information density, not the underlying ten-engine architecture.</p>
      <form className="form" onSubmit={handleSubmit(submit)}>
        <label className="field">Workspace name<input autoComplete="organization" {...register("name")} required/></label>
        <label className="field">Role<select {...register("role")}><option>Individual</option><option>Fund</option><option>Treasury</option><option>Analyst</option></select></label>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" disabled={isSubmitting}>{isSubmitting?"Opening workspace…":"Open workspace"}</button>
      </form>
      <p className="authNote">If workspace creation completes but the response is interrupted, Rivexis checks for the matching workspace before asking you to retry.</p>
    </section>
  </main>;
}

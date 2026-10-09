"use client";
import {useEffect,useState} from "react";
export function ThemeToggle(){
  const [theme,setTheme]=useState("dark");
  useEffect(()=>{const value=localStorage.getItem("rivexis_theme")==="light"?"light":"dark";setTheme(value);document.documentElement.dataset.theme=value},[]);
  function change(){const next=theme==="dark"?"light":"dark";setTheme(next);document.documentElement.dataset.theme=next;localStorage.setItem("rivexis_theme",next)}
  return <button className="themeToggle" type="button" onClick={change} aria-label={`Switch to ${theme==="dark"?"light":"dark"} mode`}>{theme==="dark"?"◐":"◑"}</button>;
}

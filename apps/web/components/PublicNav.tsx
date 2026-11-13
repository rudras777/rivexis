import {Brand} from "./Brand";
import {AuthActions} from "./AuthActions";
import {PublicNavigation} from "./PublicNavigation";

export function PublicNav(){
  return <header className="top folioNav">
    <a className="publicSkipLink" href="#main-content">Skip to content</a>
    <Brand/>
    <PublicNavigation/>
    <div className="publicActions"><AuthActions/></div>
  </header>;
}

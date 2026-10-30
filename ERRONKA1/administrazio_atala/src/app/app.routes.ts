import { Routes } from '@angular/router';
import { ErabiltzaileakComponent } from './erabiltzaileak-component/erabiltzaileak-component';
import { KargaguneakComponent } from './kargaguneak-component/kargaguneak-component';
import { ErreserbakComponent } from './erreserbak-component/erreserbak-component';

export const routes: Routes = [
    {
        path: '',
        redirectTo: 'erabiltzaileZerrenda',
        pathMatch: 'full',
    },
    {
        path: 'erabiltzaileZerrenda',
        component: ErabiltzaileakComponent,
    },
    {
        path: 'kargaguneak',
        component: KargaguneakComponent,
    },
    {
        path: 'erreserbak',
        component: ErreserbakComponent,
    },
];

import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app';

registerLocaleData(localeEs);

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));

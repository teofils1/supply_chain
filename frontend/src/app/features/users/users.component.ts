import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { ChipModule } from 'primeng/chip';
import { TooltipModule } from 'primeng/tooltip';
import {
  FormsModule,
  ReactiveFormsModule,
  FormBuilder,
  Validators,
} from '@angular/forms';
import {
  UserManagementService,
  AppUser,
  UserRole,
} from '../../core/services/user-management.service';
import { TranslateModule } from '@ngx-translate/core';

interface NewUserFormValue {
  username: string;
  name: string;
  email: string;
  initialRole: UserRole | null;
}

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [
    CommonModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    TagModule,
    ChipModule,
    TooltipModule,
    FormsModule,
    ReactiveFormsModule,
    TranslateModule,
  ],
  templateUrl: './users.component.html',
})
export class UsersComponent {
  private svc = inject(UserManagementService);
  private fb = inject(FormBuilder);

  roles: UserRole[] = ['Operator', 'Auditor', 'Admin'];
  users = this.svc.users;

  // Dialog state signals
  displayAdd = signal(false);
  displayEdit = signal(false);
  displayDelete = signal(false);
  editingUser = signal<AppUser | null>(null);
  deletingUser = signal<AppUser | null>(null);

  addForm = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    first_name: ['', [Validators.required, Validators.minLength(2)]],
    last_name: [''],
    email: ['', [Validators.required, Validators.email]],
    initialRole: [null as UserRole | null, [Validators.required]],
  });

  editForm = this.fb.nonNullable.group({
    first_name: ['', [Validators.required, Validators.minLength(2)]],
    last_name: [''],
    email: ['', [Validators.required, Validators.email]],
    active_role: [null as UserRole | null, [Validators.required]],
    roles: [[] as UserRole[]],
  });

  get addDisabled() {
    return this.addForm.invalid;
  }
  get editDisabled() {
    return this.editForm.invalid;
  }

  openAdd() {
    this.addForm.reset({
      username: '',
      first_name: '',
      last_name: '',
      email: '',
      initialRole: null,
    });
    this.displayAdd.set(true);
  }

  submitAdd() {
    if (this.addForm.invalid) return;
    const v: any = this.addForm.getRawValue();
    this.svc
      .create({
        username: v.username,
        first_name: v.first_name,
        last_name: v.last_name,
        email: v.email,
        initial_role: v.initialRole,
      })
      .subscribe((user) => {
        this.displayAdd.set(false);
        this.openEdit(user);
      });
  }

  rowClick(user: AppUser | AppUser[] | undefined) {
    if (!user || Array.isArray(user)) return;
    this.openEdit(user);
  }

  openEdit(user: AppUser) {
    this.editingUser.set(user);
    this.editForm.reset({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email,
      active_role: user.active_role,
      roles: [...user.roles],
    });
    this.displayEdit.set(true);
  }

  toggleRole(role: UserRole) {
    const roles = this.editForm.controls.roles.value;
    if (roles.includes(role)) {
      if (this.editForm.controls.active_role.value === role) return;
      this.editForm.controls.roles.setValue(roles.filter((r) => r !== role));
    } else {
      this.editForm.controls.roles.setValue([...roles, role]);
    }
  }

  submitEdit() {
    if (this.editForm.invalid) return;
    const user = this.editingUser();
    if (!user) return;
    const { first_name, last_name, email, active_role, roles } =
      this.editForm.getRawValue();
    this.svc
      .update(user.id, {
        first_name,
        last_name,
        email,
        active_role: active_role!,
        roles,
      })
      .subscribe((updated) => {
        this.editingUser.set(updated);
        this.displayEdit.set(false);
      });
  }

  confirmDelete(user: AppUser) {
    this.deletingUser.set(user);
    this.displayDelete.set(true);
  }

  deleteUser() {
    const user = this.deletingUser();
    if (!user) return;

    this.svc.delete(user.id).subscribe(() => {
      this.displayDelete.set(false);
      this.deletingUser.set(null);
    });
  }

  constructor() {
    // load users initially
    this.svc.load().subscribe();
  }
}

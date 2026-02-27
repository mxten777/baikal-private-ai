/**
 * Admin - UsersPage - 프리미엄 사용자 관리
 */
import React, { useState, useEffect } from 'react';
import { usersAPI } from '../../api/client';
import toast from 'react-hot-toast';
import {
  HiOutlinePlus,
  HiOutlineTrash,
  HiOutlineUser,
  HiOutlineUserGroup,
  HiOutlineShieldCheck,
  HiOutlineXMark,
} from 'react-icons/hi2';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', role: 'user' });

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    try { const res = await usersAPI.list(); setUsers(res.data); }
    catch { toast.error('사용자 목록 로드 실패'); }
    finally { setLoading(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.username || !form.password) { toast.error('아이디와 비밀번호를 입력하세요'); return; }
    try {
      await usersAPI.create(form);
      toast.success('사용자 생성 완료');
      setShowCreate(false); setForm({ username: '', password: '', role: 'user' }); loadUsers();
    } catch (err) { toast.error(err.response?.data?.detail || '생성 실패'); }
  };

  const handleDelete = async (user) => {
    if (!window.confirm(`${user.username} 사용자를 삭제하시겠습니까?`)) return;
    try { await usersAPI.delete(user.id); toast.success('삭제 완료'); loadUsers(); }
    catch (err) { toast.error(err.response?.data?.detail || '삭제 실패'); }
  };

  const handleToggleRole = async (user) => {
    const newRole = user.role === 'admin' ? 'user' : 'admin';
    try { await usersAPI.update(user.id, { role: newRole }); toast.success(`권한 변경: ${newRole}`); loadUsers(); }
    catch { toast.error('권한 변경 실패'); }
  };

  const handleToggleActive = async (user) => {
    try { await usersAPI.update(user.id, { is_active: !user.is_active }); toast.success(user.is_active ? '비활성화' : '활성화'); loadUsers(); }
    catch { toast.error('상태 변경 실패'); }
  };

  const stats = {
    total: users.length,
    admins: users.filter((u) => u.role === 'admin').length,
    active: users.filter((u) => u.is_active).length,
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 animate-fade-in">
      <div className="max-w-5xl mx-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6 sm:mb-8">
          <div>
            <h1 className="text-xl sm:text-[28px] font-extrabold text-gray-900 tracking-tight">사용자 관리</h1>
            <p className="text-sm text-gray-400 mt-1 font-medium">시스템 사용자 계정 관리</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
              showCreate
                ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                : 'bg-gradient-to-r from-baikal-600 to-baikal-700 text-white hover:from-baikal-700 hover:to-baikal-800 shadow-sm hover:shadow-md'
            }`}
          >
            {showCreate ? <><HiOutlineXMark className="w-4 h-4" />취소</> : <><HiOutlinePlus className="w-4 h-4" />사용자 추가</>}
          </button>
        </div>

        {/* 통계 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
          {[
            { label: '전체 사용자', value: stats.total, icon: HiOutlineUserGroup, gradient: 'from-baikal-600 to-blue-600' },
            { label: '관리자', value: stats.admins, icon: HiOutlineShieldCheck, gradient: 'from-purple-600 to-fuchsia-600' },
            { label: '활성 사용자', value: stats.active, icon: HiOutlineUser, gradient: 'from-emerald-600 to-teal-600' },
          ].map((stat) => (
            <div key={stat.label} className="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-soft transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${stat.gradient} flex items-center justify-center`}>
                  <stat.icon className="w-5 h-5 text-white" />
                </div>
              </div>
              <p className="text-3xl font-black text-gray-900 tracking-tight">{stat.value}</p>
              <p className="text-[11px] text-gray-400 font-semibold mt-0.5 uppercase tracking-[0.06em]">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* 생성 폼 */}
        {showCreate && (
          <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 animate-fade-in-up">
            <h3 className="text-[15px] font-bold text-gray-800 mb-4 flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg bg-baikal-50 flex items-center justify-center">
                <HiOutlinePlus className="w-3.5 h-3.5 text-baikal-600" />
              </div>
              새 사용자
            </h3>
            <form onSubmit={handleCreate} className="flex flex-col sm:flex-row gap-3 sm:items-end">
              <div className="flex-1">
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em] mb-1.5">아이디</label>
                <input type="text" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:border-baikal-300 focus:ring-4 focus:ring-baikal-500/10 transition-all" placeholder="사용자 아이디" />
              </div>
              <div className="flex-1">
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em] mb-1.5">비밀번호</label>
                <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:border-baikal-300 focus:ring-4 focus:ring-baikal-500/10 transition-all" placeholder="비밀번호" />
              </div>
              <div className="w-full sm:w-32">
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em] mb-1.5">권한</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:border-baikal-300 focus:ring-4 focus:ring-baikal-500/10 transition-all">
                  <option value="user">사용자</option>
                  <option value="admin">관리자</option>
                </select>
              </div>
              <button type="submit" className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-baikal-600 to-baikal-700 text-white text-sm font-semibold hover:from-baikal-700 hover:to-baikal-800 shadow-sm hover:shadow-md transition-all w-full sm:w-auto">생성</button>
            </form>
          </div>
        )}

        {/* 사용자 목록 */}
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-50">
            <div className="flex items-center gap-3">
              <h2 className="text-[15px] font-bold text-gray-800">사용자 목록</h2>
              <span className="px-2 py-0.5 rounded-lg bg-gray-100 text-[11px] font-bold text-gray-500">{users.length}</span>
            </div>
          </div>

          {loading ? (
            <div className="p-16 text-center">
              <div className="shimmer w-48 h-4 mx-auto mb-3 rounded" />
              <div className="shimmer w-32 h-4 mx-auto rounded" />
            </div>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="border-b border-gray-50">
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em]">사용자</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em]">권한</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em]">상태</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em] hidden sm:table-cell">생성일</th>
                  <th className="px-4 sm:px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-4 sm:px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-baikal-500 to-purple-600 flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
                          {user.username?.slice(0, 2).toUpperCase()}
                        </div>
                        <span className="text-[13px] font-semibold text-gray-800 truncate max-w-[80px] sm:max-w-none">{user.username}</span>
                      </div>
                    </td>
                    <td className="px-4 sm:px-6 py-4">
                      <button onClick={() => handleToggleRole(user)} className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                        user.role === 'admin' ? 'bg-purple-50 text-purple-700 hover:bg-purple-100' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                      }`}>{user.role === 'admin' ? '관리자' : '사용자'}</button>
                    </td>
                    <td className="px-4 sm:px-6 py-4">
                      <button onClick={() => handleToggleActive(user)} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                        user.is_active ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' : 'bg-red-50 text-red-700 hover:bg-red-100'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-emerald-500' : 'bg-red-500'}`} />
                        {user.is_active ? '활성' : '비활성'}
                      </button>
                    </td>
                    <td className="px-4 sm:px-6 py-4 text-[13px] text-gray-400 hidden sm:table-cell">{new Date(user.created_at).toLocaleDateString('ko-KR')}</td>
                    <td className="px-4 sm:px-6 py-4">
                      <button onClick={() => handleDelete(user)} className="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all" title="삭제">
                        <HiOutlineTrash className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

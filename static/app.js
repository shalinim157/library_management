document.addEventListener("DOMContentLoaded", () => {
  loadCategories();
  loadMembers();
  loadBooks();
  loadRecords();

  document.getElementById("member-form").addEventListener("submit", createMember);
  document.getElementById("category-form").addEventListener("submit", createCategory);
  document.getElementById("book-form").addEventListener("submit", createBook);
  document.getElementById("search-btn").addEventListener("click", () => loadBooks());
});

function showAlert(msg, isError = false) {
  const box = document.getElementById("alert-box");
  box.textContent = msg;
  box.className = `alert ${isError ? "alert-error" : "alert-success"}`;
  setTimeout(() => {
    box.className = "alert hidden";
  }, 4000);
}

// 1. Categories
async function loadCategories() {
  try {
    const res = await fetch("https://library-management-api-8co7.onrender.com/api/categories");
    // const res = await fetch("/api/categories");
    const categories = await res.json();
    const select = document.getElementById("b-category");
    select.innerHTML = '<option value="">Select Category</option>';
    categories.forEach((c) => {
      select.innerHTML += `<option value="${c.id}">${c.name}</option>`;
    });
  } catch (err) {
    console.error("Failed to load categories", err);
  }
}

async function createCategory(e) {
  e.preventDefault();
  const input = document.getElementById("c-name");
  const name = input.value.trim();
  if (!name) return;

  try {
    const res = await fetch("https://library-management-api-8co7.onrender.com/api/categories",{
    // const res = await fetch("/api/categories", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name })
    });
    const data = await res.json();
    if (!res.ok) return showAlert(data.detail || "Error creating category", true);

    showAlert("Category added!");
    input.value = "";
    loadCategories();
  } catch (err) {
    showAlert("Network error", true);
  }
}

// 2. Members
async function loadMembers() {
  try {
    const res = await fetch("https://library-management-api-8co7.onrender.com/api/members");
    // const res = await fetch("/api/members");
    const members = await res.json();
    const list = document.getElementById("members-list");
    list.innerHTML = "";
    members.forEach((m) => {
      list.innerHTML += `<li><strong>${m.name}</strong> (${m.student_id}) - ${m.email}</li>`;
    });
  } catch (err) {
    console.error("Failed to load members", err);
  }
}

async function createMember(e) {
  e.preventDefault();
  const payload = {
    student_id: document.getElementById("m-id").value,
    name: document.getElementById("m-name").value,
    email: document.getElementById("m-email").value
  };

  try {
    const res = await fetch("https://library-management-api-8co7.onrender.com/api/members",{
    // const res = await fetch("/api/members", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) return showAlert(data.detail || "Error creating student", true);

    showAlert("Student registered!");
    document.getElementById("member-form").reset();
    loadMembers();
    loadBooks(); // Refreshes dropdown options
  } catch (err) {
    showAlert("Network error", true);
  }
}

// 3. Books
async function loadBooks() {
  try {
    const search = document.getElementById("search-input").value;

    const BASE_URL = "https://library-management-api-8co7.onrender.com";
// Build full URL with search query if present
    const url = search 
      ? `${BASE_URL}/api/books?search=${encodeURIComponent(search)}` 
      : `${BASE_URL}/api/books`;
    // const url = search ? `/api/books?search=${encodeURIComponent(search)}` : "/api/books";
    const res = await fetch(url);
    const books = await res.json();
    const memberRes = await fetch("https://library-management-api-8co7.onrender.com/api/members");
    // const memberRes = await fetch("/api/members");
    const members = await memberRes.json();

    const tbody = document.getElementById("books-table-body");
    tbody.innerHTML = "";

    books.forEach((b) => {
      let memberOptions = members.map((m) => `<option value="${m.id}">${m.name}</option>`).join("");
      tbody.innerHTML += `
        <tr>
          <td><strong>${b.title}</strong></td>
          <td>${b.author}</td>
          <td>${b.isbn}</td>
          <td>${b.category ? b.category.name : "N/A"}</td>
          <td>${b.available_copies} / ${b.total_copies}</td>
          <td>
            ${
              b.available_copies > 0 && members.length > 0
                ? `<select id="borrow-member-${b.id}">${memberOptions}</select>
                   <button onclick="borrowBook(${b.id})" class="btn btn-sm">Borrow</button>`
                : b.available_copies === 0
                ? '<span style="color:red;">Out of Stock</span>'
                : '<span style="color:gray;">Register a Student First</span>'
            }
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error("Failed to load books", err);
  }
}

async function createBook(e) {
  e.preventDefault();
  const payload = {
    title: document.getElementById("b-title").value,
    author: document.getElementById("b-author").value,
    isbn: document.getElementById("b-isbn").value,
    category_id: parseInt(document.getElementById("b-category").value) || null,
    total_copies: parseInt(document.getElementById("b-copies").value) || 1
  };

  try {
    const res = await fetch("https://library-management-api-8co7.onrender.com/api/books",{
    // const res = await fetch("/api/books", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) return showAlert(data.detail || "Error adding book", true);

    showAlert("Book added!");
    document.getElementById("book-form").reset();
    loadBooks();
  } catch (err) {
    showAlert("Network error", true);
  }
}

// 4. Borrowing & Returning
async function borrowBook(bookId) {
  const memberSelect = document.getElementById(`borrow-member-${bookId}`);
  if (!memberSelect) return showAlert("No student selected", true);

  const memberId = memberSelect.value;
  try {
      const res = await fetch("https://library-management-api-8co7.onrender.com/api/borrow",{
    // const res = await fetch("/api/borrow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id: parseInt(memberId), book_id: bookId })
    });
    const data = await res.json();
    if (!res.ok) return showAlert(data.detail || "Error borrowing book", true);

    showAlert("Book borrowed!");
    loadBooks();
    loadRecords();
  } catch (err) {
    showAlert("Network error", true);
  }
}

async function loadRecords() {
  try {
    const res = await fetch("https://library-management-api-8co7.onrender.com/api/records");
    // const res = await fetch("/api/records");
    const records = await res.json();
    const tbody = document.getElementById("records-table-body");
    tbody.innerHTML = "";

    records.forEach((r) => {
      tbody.innerHTML += `
        <tr>
          <td>#${r.id}</td>
          <td>${r.member.name} (${r.member.student_id})</td>
          <td>${r.book.title}</td>
          <td>${r.borrow_date}</td>
          <td>${r.due_date}</td>
          <td><strong>${r.status}</strong></td>
          <td>$${r.fine_amount.toFixed(2)}</td>
          <td>
            ${
              r.status === "BORROWED"
                ? `<button onclick="returnBook(${r.id})" class="btn btn-sm btn-danger">Return</button>`
                : "Returned"
            }
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error("Failed to load records", err);
  }
}

// static/app.js

// static/app.js
async function returnBook(recordId) {
  try {
    // https://library-management-api-8co7.onrender.com
    const res = await fetch(`https://library-management-api-8co7.onrender.com/return/api/return/${recordId}`,{
    // Ensure the path matches /api/return/1 exactly
    // const res = await fetch(`/api/return/${recordId}`, { 
      method: "POST" 
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      return showAlert(data.detail || "Error returning book", true);
    }

    showAlert(`Book returned! Fine calculated: $${data.fine_amount.toFixed(2)}`);
    loadBooks();
    loadRecords();
  } catch (err) {
    showAlert("Network error returning book", true);
  }
}
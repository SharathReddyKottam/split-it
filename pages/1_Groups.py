import streamlit as st
import pandas as pd
from utils.file_helpers import load_groups, save_group, delete_group

# --- PAGE CONFIG ---
st.set_page_config(page_title="Groups", page_icon="👥", layout="centered")

st.title("👥 Groups")
st.write("Create and manage your expense groups.")

st.divider()

# --- CREATE A NEW GROUP ---
st.subheader("➕ Create a New Group")

group_name = st.text_input("Group name (e.g. 'Roommates', 'Trip to NYC')")

num_members = st.slider("Number of members", min_value=2, max_value=10, value=3)

members = []
for i in range(num_members):
    member = st.text_input(f"Member {i + 1} name", value=f"Person {i + 1}", key=f"member_{i}")
    members.append(member)

if st.button("✅ Create Group"):
    if group_name.strip() == "":
        st.error("❌ Please enter a group name!")
    else:
        # check if group already exists
        existing = load_groups()
        if group_name in existing["Group"].values:
            st.error(f"❌ A group called '{group_name}' already exists!")
        else:
            save_group(group_name, members)
            st.success(f"✅ Group '{group_name}' created with {num_members} members!")

st.divider()

# --- VIEW EXISTING GROUPS ---
st.subheader("📋 Your Groups")

groups_df = load_groups()

if groups_df.empty:
    st.info("No groups yet. Create one above!")
else:
    # get unique group names
    group_names = groups_df["Group"].unique()

    for group in group_names:
        # get members of this group
        members_list = groups_df[groups_df["Group"] == group]["Member"].tolist()

        # show each group in an expander
        with st.expander(f"👥 {group} — {len(members_list)} members"):
            st.write("**Members:**")

            # show members as chips
            cols = st.columns(len(members_list))
            for i, member in enumerate(members_list):
                with cols[i]:
                    st.success(member)

            st.write("")

            # delete button
            if st.button(f"🗑️ Delete '{group}'", key=f"delete_{group}"):
                delete_group(group)
                st.warning(f"🗑️ Group '{group}' deleted!")
                st.rerun()
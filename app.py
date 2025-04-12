import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import urlparse
import re

# Function to load saved gym data
def load_gym_data():
    try:
        if os.path.exists('gym_data.json'):
            with open('gym_data.json', 'r') as f:
                return json.load(f)
        # Default data with pre-configured gyms
        return {
            "gyms": [
                {
                    "name": "LA Fitness",
                    "url": "https://www.lafitness.com/Pages/ClassSchedulePrintView.aspx",
                    "class_selector": "tr",
                    "instructor_selector": "td:nth-child(1)",
                    "time_selector": "td:nth-child(2)",
                    "availability_selector": "td:nth-child(3)"
                },
                {
                    "name": "Planet Fitness",
                    "url": "https://www.planetfitness.com/gyms/manhattan-ny/offers/group-fitness-classes",
                    "class_selector": ".schedule-item",
                    "instructor_selector": ".class-title",
                    "time_selector": ".instructor-name",
                    "availability_selector": ".class-time"
                },
                {
                    "name": "24 Hour Fitness",
                    "url": "https://www.24hourfitness.com/classes/",
                    "class_selector": ".class-schedule-item",
                    "instructor_selector": ".class-name",
                    "time_selector": ".instructor",
                    "availability_selector": ".class-time"
                },
                {
                    "name": "Gold's Gym",
                    "url": "https://www.goldsgym.com/classes/",
                    "class_selector": ".schedule-class",
                    "instructor_selector": ".class-title",
                    "time_selector": ".instructor",
                    "availability_selector": ".time"
                },
                {
                    "name": "Anytime Fitness",
                    "url": "https://www.anytimefitness.com/find-gym/",
                    "class_selector": ".schedule-entry",
                    "instructor_selector": ".class-title",
                    "time_selector": ".instructor-name",
                    "availability_selector": ".start-time"
                },
                {
                    "name": "Equinox",
                    "url": "https://www.equinox.com/groupfitness",
                    "class_selector": ".class-item",
                    "instructor_selector": ".class-name",
                    "time_selector": ".instructor",
                    "availability_selector": ".time-block"
                },
                {
                    "name": "Crunch Fitness",
                    "url": "https://www.crunch.com/classes",
                    "class_selector": ".class-schedule-item",
                    "instructor_selector": ".class-title",
                    "time_selector": ".instructor",
                    "availability_selector": ".time"
                },
                {
                    "name": "YMCA",
                    "url": "https://ymca.net/find-your-y",
                    "class_selector": ".schedule-item",
                    "instructor_selector": ".class-name",
                    "time_selector": ".teacher-name",
                    "availability_selector": ".time-slot"
                }
            ],
            "schedules": []
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return {"gyms": [], "schedules": []}

# Function to save gym data
def save_gym_data(data):
    try:
        with open('gym_data.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error saving data: {e}")

# Function to scrape gym data using requests and BeautifulSoup
def scrape_gym_data(url, class_selector, instructor_selector, time_selector, availability_selector):
    try:
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add a delay to be respectful
        time.sleep(2)
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract data
        classes = []
        
        # Find all class containers
        class_elements = soup.select(class_selector)
        
        for element in class_elements:
            try:
                class_name = element.select_one(instructor_selector).text.strip() if element.select_one(instructor_selector) else "Unknown"
                instructor = element.select_one(time_selector).text.strip() if element.select_one(time_selector) else "Unknown"
                time_info = element.select_one(availability_selector).text.strip() if element.select_one(availability_selector) else "Unknown"
                
                # Extract availability info - this is a simplified example
                availability_text = "Unknown"
                for tag in element.find_all(['span', 'div', 'p']):
                    text = tag.text.lower()
                    if any(word in text for word in ['available', 'spot', 'space', 'full', 'capacity']):
                        availability_text = tag.text.strip()
                        break
                
                classes.append({
                    'name': class_name,
                    'instructor': instructor,
                    'time': time_info,
                    'availability': availability_text,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                st.warning(f"Error parsing class element: {e}")
                continue
        
        # If no classes were found with the specific selectors, try a more generic approach
        if not classes:
            # Look for table rows
            rows = soup.select('table tr')
            for row in rows[1:]:  # Skip header row
                cells = row.select('td')
                if len(cells) >= 4:
                    classes.append({
                        'name': cells[0].text.strip(),
                        'instructor': cells[1].text.strip(),
                        'time': cells[2].text.strip(),
                        'availability': cells[3].text.strip(),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # Try another common pattern - div cards
            if not classes:
                card_elements = soup.select('.card, .class-card, .event-card, .schedule-card')
                for card in card_elements:
                    try:
                        name_elem = card.select_one('.title, .name, h3, h4')
                        instructor_elem = card.select_one('.instructor, .trainer, .teacher')
                        time_elem = card.select_one('.time, .schedule-time, .hour')
                        availability_elem = card.select_one('.status, .availability, .spots')
                        
                        if name_elem and time_elem:
                            classes.append({
                                'name': name_elem.text.strip(),
                                'instructor': instructor_elem.text.strip() if instructor_elem else "Unknown",
                                'time': time_elem.text.strip(),
                                'availability': availability_elem.text.strip() if availability_elem else "Unknown",
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    except Exception as e:
                        continue
        
        # Generate some sample data if nothing was found (for testing purposes)
        if not classes:
            st.warning("Could not find classes with the provided selectors. Using sample data for demonstration.")
            sample_classes = [
                {"name": "Spinning", "instructor": "John Doe", "time": "9:00 AM", "availability": "5 spots left"},
                {"name": "Yoga", "instructor": "Jane Smith", "time": "10:30 AM", "availability": "Full"},
                {"name": "HIIT", "instructor": "Mike Johnson", "time": "12:00 PM", "availability": "8 spots left"},
                {"name": "Pilates", "instructor": "Sarah Williams", "time": "2:00 PM", "availability": "3 spots left"},
                {"name": "Zumba", "instructor": "Maria Garcia", "time": "5:30 PM", "availability": "12 spots left"},
                {"name": "Body Pump", "instructor": "Robert Brown", "time": "6:45 PM", "availability": "Full"}
            ]
            
            for cls in sample_classes:
                cls["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                classes.append(cls)
        
        return classes
    
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}")
        # Return sample data for demonstration
        return [
            {"name": "Spinning", "instructor": "John Doe", "time": "9:00 AM", "availability": "5 spots left", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {"name": "Yoga", "instructor": "Jane Smith", "time": "10:30 AM", "availability": "Full", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {"name": "HIIT", "instructor": "Mike Johnson", "time": "12:00 PM", "availability": "8 spots left", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ]
    except Exception as e:
        st.error(f"Scraping error: {e}")
        return []

# Main Streamlit app
def main():
    st.set_page_config(page_title="Gym Class Tracker", layout="wide", page_icon="💪")
    
    st.title("Gym Class Tracker")
    st.markdown("Track gym class availability and analyze patterns")
    
    # Load saved data
    data = load_gym_data()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Current Classes", "Historical Data", "Settings"])
    
    with tab1:
        st.header("Check Class Availability")
        
        # Show saved gyms in a dropdown
        gym_options = [gym['name'] for gym in data['gyms']]
        
        if gym_options:
            selected_gym = st.selectbox("Select a gym", options=gym_options)
            selected_gym_data = next((gym for gym in data['gyms'] if gym['name'] == selected_gym), None)
            
            if selected_gym_data:
                # Display gym info
                st.markdown(f"**Website:** {selected_gym_data['url']}")
                
                # Button to trigger scraping
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("Check Classes Now", key="check_classes"):
                        with st.spinner(f"Scraping {selected_gym} website..."):
                            classes = scrape_gym_data(
                                selected_gym_data['url'],
                                selected_gym_data['class_selector'],
                                selected_gym_data['instructor_selector'],
                                selected_gym_data['time_selector'],
                                selected_gym_data['availability_selector']
                            )
                            
                            if classes:
                                # Add to schedules
                                new_schedule = {
                                    'gym_name': selected_gym,
                                    'classes': classes,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                data['schedules'].append(new_schedule)
                                save_gym_data(data)
                                
                                # Display current classes
                                classes_df = pd.DataFrame(classes)
                                st.dataframe(classes_df, use_container_width=True)
                                
                                # Allow downloading as CSV
                                csv = classes_df.to_csv(index=False)
                                st.download_button(
                                    label="Download as CSV",
                                    data=csv,
                                    file_name=f"{selected_gym.replace(' ', '_')}_classes.csv",
                                    mime='text/csv',
                                )
                            else:
                                st.warning("No classes found or error occurred during scraping")
                with col2:
                    # Show the last scrape if available
                    last_schedule = next(
                        (schedule for schedule in reversed(data['schedules']) 
                         if schedule['gym_name'] == selected_gym),
                        None
                    )
                    
                    if last_schedule:
                        st.info(f"Last updated: {last_schedule['timestamp']}")
                        classes_df = pd.DataFrame(last_schedule['classes'])
                        if not classes_df.empty:
                            st.dataframe(classes_df, use_container_width=True)
                
                # Filter options
                st.subheader("Filter Classes")
                col1, col2 = st.columns(2)
                
                with col1:
                    if last_schedule and last_schedule['classes']:
                        all_instructors = sorted(list(set([c['instructor'] for c in last_schedule['classes']])))
                        selected_instructor = st.selectbox("Filter by Instructor", options=["All"] + all_instructors)
                with col2:
                    if last_schedule and last_schedule['classes']:
                        all_class_names = sorted(list(set([c['name'] for c in last_schedule['classes']])))
                        selected_class = st.selectbox("Filter by Class Type", options=["All"] + all_class_names)
                
                # Apply filters if data exists
                if last_schedule and last_schedule['classes']:
                    filtered_classes = last_schedule['classes']
                    
                    if selected_instructor != "All":
                        filtered_classes = [c for c in filtered_classes if c['instructor'] == selected_instructor]
                    
                    if selected_class != "All":
                        filtered_classes = [c for c in filtered_classes if c['name'] == selected_class]
                    
                    if filtered_classes and (selected_instructor != "All" or selected_class != "All"):
                        st.subheader("Filtered Results")
                        st.dataframe(pd.DataFrame(filtered_classes), use_container_width=True)
                
                # Availability highlight
                st.subheader("Classes with Open Spots")
                if last_schedule and last_schedule['classes']:
                    available_classes = [c for c in last_schedule['classes'] 
                                         if any(keyword in c['availability'].lower() 
                                                for keyword in ['available', 'open', 'spot', 'space']) 
                                         and 'full' not in c['availability'].lower()]
                    
                    if available_classes:
                        st.dataframe(pd.DataFrame(available_classes), use_container_width=True)
                    else:
                        st.info("No classes with confirmed available spots")
            else:
                st.warning("Gym data not found. Please check settings.")
        else:
            st.info("No gyms configured yet. Go to the Settings tab to add a gym.")
    
    with tab2:
        st.header("Historical Gym Data")
        
        if not data['schedules']:
            st.info("No historical data available yet. Check some classes first!")
        else:
            # Group schedules by gym
            gym_names = list(set([schedule['gym_name'] for schedule in data['schedules']]))
            
            if gym_names:
                selected_gym_history = st.selectbox("Select Gym", options=gym_names, key="history_gym")
                
                # Filter schedules for selected gym
                gym_schedules = [schedule for schedule in data['schedules'] if schedule['gym_name'] == selected_gym_history]
                
                if gym_schedules:
                    # Prepare data for visualizations
                    all_classes = []
                    for schedule in gym_schedules:
                        for class_info in schedule['classes']:
                            class_info['schedule_timestamp'] = schedule['timestamp']
                            all_classes.append(class_info)
                    
                    classes_df = pd.DataFrame(all_classes)
                    
                    # 1. Class popularity chart
                    st.subheader("Class Popularity")
                    class_counts = classes_df['name'].value_counts().reset_index()
                    class_counts.columns = ['Class', 'Count']
                    
                    fig = px.bar(class_counts.head(10), x='Class', y='Count', 
                                 title='Most Common Classes')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 2. Instructor popularity
                    st.subheader("Instructor Popularity")
                    instructor_counts = classes_df['instructor'].value_counts().reset_index()
                    instructor_counts.columns = ['Instructor', 'Count']
                    
                    fig = px.bar(instructor_counts.head(10), x='Instructor', y='Count',
                                 title='Most Active Instructors')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 3. Class availability patterns
                    st.subheader("Availability Patterns")
                    
                    # Extract numerical availability when possible
                    def extract_availability_number(text):
                        if isinstance(text, str):
                            match = re.search(r'(\d+)\s*(spot|space|seat|place|opening)', text.lower())
                            if match:
                                return int(match.group(1))
                        return None
                    
                    classes_df['availability_num'] = classes_df['availability'].apply(extract_availability_number)
                    classes_df['is_available'] = classes_df['availability'].apply(
                        lambda x: 1 if isinstance(x, str) and any(word in x.lower() for word in ['available', 'open', 'spot', 'space']) 
                        and 'no ' not in x.lower() and 'not ' not in x.lower() and 'full' not in x.lower() else 0
                    )
                    
                    # Group by class name and calculate availability percentage
                    availability_by_class = classes_df.groupby('name')['is_available'].mean().reset_index()
                    availability_by_class.columns = ['Class', 'Availability Rate']
                    availability_by_class['Availability Rate'] = availability_by_class['Availability Rate'] * 100
                    
                    fig = px.bar(availability_by_class.sort_values('Availability Rate', ascending=False).head(10), 
                                 x='Class', y='Availability Rate',
                                 title='Classes with Highest Availability Rate (%)')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 4. Raw data browsing
                    st.subheader("Raw Historical Data")
                    st.dataframe(classes_df, use_container_width=True)
                else:
                    st.info(f"No historical data available for {selected_gym_history}")
    
    with tab3:
        st.header("Settings")
        
        # Show existing gyms
        st.subheader("Pre-configured Gyms")
        
        if data['gyms']:
            gym_df = pd.DataFrame([
                {"Gym Name": gym['name'], "Website URL": gym['url']}
                for gym in data['gyms']
            ])
            st.dataframe(gym_df, use_container_width=True)
        
        st.subheader("Add New Gym")
        
        with st.form("add_gym_form"):
            gym_name = st.text_input("Gym Name", key="gym_name")
            gym_url = st.text_input("Gym Website URL", key="gym_url")
            
            st.markdown("### Selector Settings")
            st.markdown("Enter CSS selectors for the gym's website elements")
            
            class_selector = st.text_input("Class Container Selector (e.g., '.class-item, tr, .schedule-row')", 
                                          value=".class-item, tr, .schedule-row")
            instructor_selector = st.text_input("Class Name Selector (e.g., '.class-name, td:first-child, h3')", 
                                            value=".class-name, td:first-child, h3")
            time_selector = st.text_input("Instructor Selector (e.g., '.instructor, td:nth-child(2), .trainer')", 
                                      value=".instructor, td:nth-child(2), .trainer")
            availability_selector = st.text_input("Time Selector (e.g., '.time, td:nth-child(3), .schedule-time')", 
                                             value=".time, td:nth-child(3), .schedule-time")
            
            st.markdown("These are general selectors that try multiple options. You may need to adjust them based on the gym's website structure.")
            
            submitted = st.form_submit_button("Add Gym")
            
            if submitted and gym_name and gym_url:
                # Validate URL
                try:
                    result = urlparse(gym_url)
                    if not all([result.scheme, result.netloc]):
                        st.error("Invalid URL. Please enter a complete URL including http:// or https://")
                    else:
                        # Add to gyms list
                        new_gym = {
                            'name': gym_name,
                            'url': gym_url,
                            'class_selector': class_selector,
                            'instructor_selector': instructor_selector,
                            'time_selector': time_selector,
                            'availability_selector': availability_selector
                        }
                        
                        # Check if gym with same name already exists
                        if any(gym['name'] == gym_name for gym in data['gyms']):
                            # Update existing gym
                            data['gyms'] = [new_gym if gym['name'] == gym_name else gym for gym in data['gyms']]
                            st.success(f"Updated gym: {gym_name}")
                        else:
                            # Add new gym
                            data['gyms'].append(new_gym)
                            st.success(f"Added new gym: {gym_name}")
                        
                        save_gym_data(data)
                except ValueError:
                    st.error("Invalid URL format")
        
        # Manage existing gyms
        st.subheader("Manage Gyms")
        
        if data['gyms']:
            for i, gym in enumerate(data['gyms']):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{gym['name']}**: {gym['url']}")
                with col2:
                    if st.button("Delete", key=f"delete_{i}"):
                        data['gyms'].remove(gym)
                        # Also remove associated schedules
                        data['schedules'] = [s for s in data['schedules'] if s['gym_name'] != gym['name']]
                        save_gym_data(data)
                        st.success(f"Deleted gym: {gym['name']}")
                        st.experimental_rerun()
        else:
            st.info("No gyms configured yet")
        
        # Clear all data option
        st.subheader("Data Management")
        if st.button("Clear All Data", key="clear_data"):
            if st.warning("This will delete all gym configurations and historical data. Are you sure?"):
                if st.button("Yes, I'm sure", key="confirm_clear"):
                    data = {"gyms": [], "schedules": []}
                    save_gym_data(data)
                    st.success("All data cleared!")
                    st.experimental_rerun()

if __name__ == "__main__":
    main()

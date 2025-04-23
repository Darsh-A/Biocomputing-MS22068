import re
import os
import json

def readFile(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        return lines
    except FileNotFoundError:
        print(f"Error: File not found at {os.path.abspath(file_path)}")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


"""
Uses Regex with the trailing whitespaces to format the file into a JSON later
I had a headache doing this parsing :D
"""


def hasMainKeyword(line):
    """Checks if a line starts with a main keyword (uppercase, beginning of line)."""
    findMainKeyandContent = r'^([A-Z][A-Z_]+)\s+(.*)'
    match = re.match(findMainKeyandContent, line)
    if match:
        return {
            'keyword': match.group(1).strip(),
            'content': match.group(2).strip(),
            'indentation': 0
        }
    return None

def hasSubKeyword(line):
    """Checks if a line starts with an indented sub-keyword."""
    findSubKey = r'^(\s+)([A-Z][A-Z_]+)\s+(.*)'
    match = re.match(findSubKey, line)
    if match:
        if match.group(2):
             return {
                'keyword': match.group(2).strip(),
                'content': match.group(3).strip(),
                'indentation': len(match.group(1))
             }
    return None

def hasOnlyContent(line):
    """Checks if a line contains only indented content (no keyword at the start)."""
    findOnlyContent = r'^(\s+)(.+)'
    match = re.match(findOnlyContent, line)
    # Ensure it doesnt match hasSubKeyword
    if match and not re.match(r'^\s+[A-Z][A-Z_]+\s+', line):
        return {
            'content': match.group(2).strip(),
            'indentation': len(match.group(1))
        }
    return None

def findParentKeywordInfo(line_info, data, current_index):
    """
    Finds the parent keyword for an indented line.
    Searches backwards from the current line.
    """
    if line_info is None or 'indentation' not in line_info:
        return None

    current_indentation = line_info['indentation']

    for i in range(current_index - 1, -1, -1):
        prev_line = data[i]
        parent_main_info = hasMainKeyword(prev_line)
        parent_sub_info = hasSubKeyword(prev_line)

        parent_info = parent_main_info or parent_sub_info

        if parent_info and parent_info['indentation'] < current_indentation:
             return parent_info['keyword']
    return None



class GenBank:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = readFile(self.file_path)

        self.parsed_dict = {} 
        self.features = [] 
        self.sequence = ""
        self.gene_info = {}
        self.mrna_info = {}
        self.cds_info = {}

        if self.data:
            try:
                self._parse_genbank_structure()
                self._process_features()
                self._extract_sequence()
                self._post_process_info()
            except Exception as e:
                print(f"Error during GenBank parsing: {e}")
                self.parsed_dict = {}
                self.features = []
                self.sequence = ""
        else:
            print(f"Could not initialize GenBank parser because file {file_path} could not be read.")

    def _parse_genbank_structure(self):
        """Parses the overall GenBank file structure into self.parsed_dict."""
        if not self.data:
            return

        repeatable_keys = {'REFERENCE', 'COMMENT'}

        last_main_key = None
        last_sub_key_for_main = {}

        for i, line in enumerate(self.data):
            if not line.strip() or line.strip() == '//':
                continue

            main_key_info = hasMainKeyword(line)
            sub_key_info = hasSubKeyword(line)
            content_info = hasOnlyContent(line)

            if main_key_info:
                key = main_key_info['keyword']
                new_entry = {
                    'content': main_key_info['content'],
                    'subKeywords': {}
                }
                last_main_key = key
                last_sub_key_for_main[key] = None

                if key in self.parsed_dict and key in repeatable_keys:
                    if isinstance(self.parsed_dict[key], list):
                        self.parsed_dict[key].append(new_entry)
                    else:
                        self.parsed_dict[key] = [self.parsed_dict[key], new_entry]
                else:
                    self.parsed_dict[key] = new_entry

            elif sub_key_info:
                parent_key = findParentKeywordInfo(sub_key_info, self.data, i)
                if parent_key and parent_key in self.parsed_dict:
                    sub_key = sub_key_info['keyword']
                    target_entry_container = self.parsed_dict[parent_key]

                    if isinstance(target_entry_container, list):
                        target_dict = target_entry_container[-1]
                    else:
                        target_dict = target_entry_container

                    if 'subKeywords' not in target_dict: target_dict['subKeywords'] = {}

                    target_dict['subKeywords'][sub_key] = sub_key_info['content']
                    last_sub_key_for_main[parent_key] = sub_key

            elif content_info:
                parent_key = findParentKeywordInfo(content_info, self.data, i)
                if parent_key and parent_key in self.parsed_dict:
                    target_entry_container = self.parsed_dict[parent_key]
                    last_sub_key = last_sub_key_for_main.get(parent_key)

                    if isinstance(target_entry_container, list):
                        target_dict = target_entry_container[-1]
                    else:
                        target_dict = target_entry_container

                    if 'subKeywords' not in target_dict: target_dict['subKeywords'] = {}

                    if last_sub_key and last_sub_key in target_dict.get('subKeywords', {}):
                        target_dict['subKeywords'][last_sub_key] += '\n' + content_info['content']
                    else:
                         if 'content' not in target_dict: target_dict['content'] = ""
                         target_dict['content'] += '\n' + content_info['content']

    def _process_features(self):
        """Parses the FEATURES section in more detail."""
        self.features = []
        self.mrna_info = {}
        self.cds_info = {}

        if 'FEATURES' not in self.parsed_dict:
            return

        feature_section = self.parsed_dict['FEATURES']
        features_content = feature_section.get('content', '') if isinstance(feature_section, dict) else ""
        if isinstance(feature_section, list) and feature_section:
            features_content = feature_section[0].get('content', '')

        if not features_content:
            return

        features_lines = features_content.split('\n')
        current_feature_dict = None
        last_qualifier_key = None

        feature_key_pattern = re.compile(r'^\s*([a-zA-Z_]+)\s+(.*)')
        qualifier_pattern = re.compile(r'^\s+/([a-zA-Z_]+)(?:=(.*))?') # Make value optional for flags
        qualifier_continuation_pattern = re.compile(r'^\s+([^/].*)')

        for line in features_lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            feature_match = feature_key_pattern.match(line)
            qualifier_match = qualifier_pattern.match(line)
            continuation_match = None
            if not qualifier_match:
                 continuation_match = qualifier_continuation_pattern.match(line)


            if feature_match:
                if current_feature_dict:
                    self.features.append(current_feature_dict)

                current_feature_dict = {
                    "type": feature_match.group(1),
                    "location": feature_match.group(2).strip(),
                    "qualifiers": {}
                }
                last_qualifier_key = None

                if current_feature_dict["type"] == "mRNA":
                    mrna_id_tmp = f"mRNA_{len(self.mrna_info) + 1}"
                    current_feature_dict["id"] = mrna_id_tmp
                    self.mrna_info[mrna_id_tmp] = current_feature_dict
                elif current_feature_dict["type"] == "CDS":
                    cds_id_tmp = f"CDS_{len(self.cds_info) + 1}"
                    current_feature_dict["id"] = cds_id_tmp
                    self.cds_info[cds_id_tmp] = current_feature_dict

            elif qualifier_match and current_feature_dict:
                qualifier_key = qualifier_match.group(1)
                qualifier_value = qualifier_match.group(2)

                if qualifier_value is None: 
                     qualifier_value_cleaned = True 
                else:
                    qualifier_value_cleaned = qualifier_value.strip()
                    if qualifier_value_cleaned.startswith('"') and qualifier_value_cleaned.endswith('"'):
                        qualifier_value_cleaned = qualifier_value_cleaned[1:-1]

                if qualifier_key in current_feature_dict["qualifiers"]:
                    existing_value = current_feature_dict["qualifiers"][qualifier_key]
                    if isinstance(existing_value, list):
                        existing_value.append(qualifier_value_cleaned)
                    else:
                        current_feature_dict["qualifiers"][qualifier_key] = [existing_value, qualifier_value_cleaned]
                else:
                     current_feature_dict["qualifiers"][qualifier_key] = qualifier_value_cleaned

                last_qualifier_key = qualifier_key

                current_id_value = qualifier_value_cleaned if isinstance(qualifier_value_cleaned, str) else None
                if current_id_value:
                    if current_feature_dict["type"] == "gene" and qualifier_key == "gene":
                        self.gene_info["name"] = current_id_value

                    elif current_feature_dict["type"] == "mRNA" and qualifier_key == "transcript_id":

                        new_id = current_id_value
                        old_id = current_feature_dict.get("id")
                        current_feature_dict["id"] = new_id
                        if old_id and old_id in self.mrna_info: del self.mrna_info[old_id]
                        self.mrna_info[new_id] = current_feature_dict

                    elif current_feature_dict["type"] == "CDS" and qualifier_key == "protein_id":
                        
                        new_id = current_id_value
                        old_id = current_feature_dict.get("id")
                        current_feature_dict["id"] = new_id
                        if old_id and old_id in self.cds_info: del self.cds_info[old_id]
                        self.cds_info[new_id] = current_feature_dict

            elif continuation_match and current_feature_dict and last_qualifier_key:
                
                continuation_text = continuation_match.group(1).strip()

                if continuation_text.startswith('"') and continuation_text.endswith('"'):
                     continuation_text = continuation_text[1:-1]

                last_value = current_feature_dict["qualifiers"].get(last_qualifier_key)

                if isinstance(last_value, list):
                     if last_value and isinstance(last_value[-1], str):
                          last_value[-1] += continuation_text
                     else: 
                          last_value.append(continuation_text)

                elif isinstance(last_value, str):
                     current_feature_dict["qualifiers"][last_qualifier_key] += continuation_text

        if current_feature_dict:
            self.features.append(current_feature_dict)


    def _extract_sequence(self):
        """Extracts the sequence from the ORIGIN section.""" 
        self.sequence = ""
        if 'ORIGIN' not in self.parsed_dict: return  # A troublesome element for some reason

        origin_section = self.parsed_dict['ORIGIN']
        origin_content = origin_section.get('content', '') if isinstance(origin_section, dict) else ""
        if isinstance(origin_section, list) and origin_section:
             origin_content = origin_section[0].get('content', '')

        if not origin_content: return

        origin_lines = origin_content.split('\n')
        seq_pattern = re.compile(r'^\s*\d+\s+([a-zA-Z\s]+)')

        for line in origin_lines:
            match = seq_pattern.match(line)
            if match:
                seq_part = match.group(1).replace(' ', '').lower()
                self.sequence += seq_part

    def _post_process_info(self):
         """Extract additional structured info after main parsing."""
         # Organism Name:
         if 'SOURCE' in self.parsed_dict:
             source_entry = self.parsed_dict['SOURCE']
             source_dict = source_entry[0] if isinstance(source_entry, list) else source_entry
             if isinstance(source_dict, dict):
                 if 'ORGANISM' in source_dict.get('subKeywords', {}):
                     self.gene_info["organism_name"] = source_dict['subKeywords']['ORGANISM']
                 else:
                     self.gene_info["organism_name"] = source_dict.get('content', 'Unknown')
             else:
                 self.gene_info["organism_name"] = str(source_dict) # Fallback
         else:
            self.gene_info["organism_name"] = "Unknown"

         # Chromosome
         chromosome = "Unknown"
         if 'LOCUS' in self.parsed_dict:
             locus_entry = self.parsed_dict['LOCUS']
             locus_dict = locus_entry[0] if isinstance(locus_entry, list) else locus_entry
             locus_content = locus_dict.get('content', '') if isinstance(locus_dict, dict) else str(locus_dict)
             match = re.search(r'chromosome\s+(\S+)', locus_content, re.IGNORECASE)
             if match:
                 chromosome = match.group(1).strip(',').strip('.')
         # Fallback to source feature if no LOCUS 
         if chromosome == "Unknown":
             source_features = self.get_feature_by_type('source')
             if source_features:
                 qualifiers = source_features[0].get('qualifiers', {})
                 chrom_qual = qualifiers.get('chromosome')
                 if isinstance(chrom_qual, list) and chrom_qual:
                     chromosome = chrom_qual[0]
                 elif isinstance(chrom_qual, str):
                     chromosome = chrom_qual

         self.gene_info["chromosome"] = chromosome


    def get_gene_info(self):
        """Returns basic gene information."""
        return {
            "gene_name": self.gene_info.get("name", "Unknown"),
            "organism_name": self.gene_info.get("organism_name", "Unknown"),
            "chromosome": self.gene_info.get("chromosome", "Unknown")
        }

    def get_sequence(self, clean=True):
         """Returns the extracted sequence."""
         if clean:
              return self.sequence.lower().replace(" ", "")
         return self.sequence

    def get_feature_by_type(self, feature_type):
        """Returns a list of all features matching the given type."""
        return [f for f in self.features if f.get("type") == feature_type]


# Fasta Wroter Function
def write_fasta(file_path, header, sequence, line_width=70):
    """Writes sequence data to a FASTA format file."""
    try:
        with open(file_path, 'w') as f:
            f.write(f">{header}\n")
            for i in range(0, len(sequence), line_width):
                f.write(sequence[i:i+line_width] + "\n")
        print(f"Successfully wrote FASTA file: {file_path}")
    except Exception as e:
        print(f"Error writing FASTA file {file_path}: {e}")


# Execute everythign
if __name__ == "__main__":

    # Config
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        current_dir = os.getcwd()
    file_name = 'ptenSequence.gb'
    genbank_file_path = os.path.join(current_dir, file_name)

    base_name = os.path.splitext(file_name)[0]
    json_output_path = os.path.join(current_dir, f"{base_name}_parsed.json")
    fasta_output_path = os.path.join(current_dir, f"{base_name}_sequence.fasta")



    print(f"Attempting to parse GenBank file: {genbank_file_path}")
    gb_parser = GenBank(genbank_file_path)

    if gb_parser.data:
        print("\n--- Parsing Complete ---")

        output_data = {}


        output_data['metadata'] = {}
        for key, value in gb_parser.parsed_dict.items():
            if key not in ['FEATURES', 'ORIGIN']:
                output_data['metadata'][key] = value


        output_data['features'] = gb_parser.features

        output_data['sequence_info'] = {
            'length': len(gb_parser.sequence),
            'fasta_file': os.path.basename(fasta_output_path) 
        }

        # Write JSON File 
        try:
            with open(json_output_path, 'w', encoding='utf-8') as f_json:
                json.dump(output_data, f_json, indent=4)
            print(f"Successfully wrote JSON file: {json_output_path}")
        except Exception as e:
            print(f"Error writing JSON file {json_output_path}: {e}")

        # Write Fasta
        sequence = gb_parser.get_sequence(clean=True)
        if sequence:
            header = "Unknown Record"
            try:
                locus_info = output_data['metadata'].get('LOCUS', {})
                locus_dict = locus_info[0] if isinstance(locus_info, list) else locus_info
                record_id = locus_dict.get('content', '').split()[0] if isinstance(locus_dict, dict) else "UnknownID"

                def_info = output_data['metadata'].get('DEFINITION', {})
                def_dict = def_info[0] if isinstance(def_info, list) else def_info
                definition = def_dict.get('content', '') if isinstance(def_dict, dict) else str(def_dict)

                header = f"{record_id} {definition}"
            except Exception:
                 print("Warning: Could not extract detailed header info, using default.")
                 pass 
            write_fasta(fasta_output_path, header, sequence)
        else:
            print("Warning: No sequence found in ORIGIN section, FASTA file not written.")

        # Print Summary
        gene_info = gb_parser.get_gene_info()
        print("\nSummary:")
        print(f"  Gene Name: {gene_info['gene_name']}")
        print(f"  Organism: {gene_info['organism_name']}")
        print(f"  Chromosome: {gene_info['chromosome']}")
        print(f"  Sequence Length: {len(gb_parser.sequence)}")
        print(f"  Number of Features Parsed: {len(gb_parser.features)}")
        print(f"  Number of References: {len(output_data['metadata'].get('REFERENCE', []))}")

    else:
        print("\nParser initialization failed. Cannot proceed.")